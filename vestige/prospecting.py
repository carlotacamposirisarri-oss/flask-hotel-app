"""Proactive mode: find and research companies that have the problem Vestige solves.

  Lead radar   (web)  thesis -> candidate companies with the public signal behind each
  Dossier      (web)  public footprint: initiatives, clients, competitors, reports, claims,
                      press and social conversation -> problem signals with sources
  Opportunity  (AI)   dossier x Vestige's offer x Vestige's cross-brand intelligence
                      -> fit score, pitch angle, entry offer, objections, outreach drafts
Outputs: printable opportunity report, pitch deck, outreach drafts, and a one-click
conversion into a client engagement when the lead is won.
"""
import json
import threading
import traceback

from flask import current_app

from . import ai, db, diagnostic
from .prompts import VESTIGE_SYSTEM

STAGES = ["Suggested", "Identified", "Researched", "Contacted", "Meeting", "Proposal", "Won", "Lost"]
RUN_STAGES = [("research", "Researching the public footprint"), ("opportunity", "Assessing fit and crafting the pitch")]

DEFAULT_OFFER = """Vestige designs relationship strategies for luxury maisons: turning client data into behavioural
archetypes, auditing engagement & retention strategies against brand identity and competitors, and
redirecting resources into experiential programmes that deepen emotional connection with VICs and
drive commercial results. Deliverables: Engagement Diagnostic (analytical report + deck),
experiential strategy & 12-month roadmap, archetype-led clienteling playbooks, ongoing intelligence."""

RESEARCH_SYSTEM = VESTIGE_SYSTEM + """

Research rules: use web search and fetch to build an evidence-based view of a COMPANY from public
sources (official site, press releases, annual/ESG reports, interviews, trade press, social media
posts and public comments, reviews, events coverage). Cite a source URL for every factual claim.
Distinguish fact from inference. Never profile private individuals; refer to executives only by
public role and public statements."""

RADAR_PROMPT = """## Vestige's offer
{offer}

## Search thesis
{thesis}

## Already in the pipeline (exclude)
{existing}

## Task
Find {n} real companies (luxury maisons, hospitality groups or premium brands) that match the
thesis and show PUBLIC signals of the problem Vestige solves: transactional or generic client
engagement, retention or next-gen drift, experiential gaps, community deficits, competitive
pressure on their top clients, leadership statements about clienteling or experiences, new
markets/openings needing relationship strategy.

## Output
JSON: {{"candidates": [{{"company": str, "sector": str, "market": str, "website": str,
  "signal": str (the specific public signal, dated), "source_url": str,
  "why_vestige": str (one sentence), "fit_score": int 0-100}}]}}
"""

DOSSIER_PROMPT = """## Company
{company} — sector: {sector} — market: {market} — website: {website}

## Material Vestige already gathered (may include pasted posts, reports, notes)
{material}

## Task
Research this company's public footprint over roughly the last 24 months and build a dossier.
Look for: positioning & heritage; strategic initiatives (openings, programmes, launches,
memberships, loyalty, events, collaborations, digital); who their clients are publicly said to be;
competitors and the competitors' recent experiential/clienteling moves; reports, results calls and
leadership claims; press coverage; social media conversation and client comments. Then extract
PROBLEM SIGNALS relevant to client engagement, retention and experience.

## Output
JSON: {{
  "snapshot": {{"positioning": str, "heritage": str, "markets": str, "scale_signals": str, "leadership_priorities": str}},
  "initiatives": [{{"initiative": str, "date": str, "type": str, "source": str}}],
  "client_signals": [{{"signal": str, "source": str}}],
  "competitors": [{{"name": str, "recent_actions": str, "source": str}}],
  "claims_and_reports": [{{"claim": str, "who": str (public role), "date": str, "source": str}}],
  "sentiment": {{"summary": str, "themes": [str], "sources": [str]}},
  "problem_signals": [{{"signal": str, "evidence": str, "source": str,
                        "problem_type": "retention|engagement|generic experiences|community|next-gen|competitive pressure|new market|data & clienteling",
                        "severity": "low|medium|high", "fact_or_inference": "fact|inference"}}],
  "likely_archetypes": [{{"name": str, "rationale": str}}],
  "caveats": str
}}
"""

OPPORTUNITY_PROMPT = """## Vestige's offer
{offer}

## What Vestige has learned across its engagements (anonymised)
{patterns}

## Dossier on {company}
{dossier}

## Task
Decide whether and how Vestige should approach {company}. Be honest: a low fit is a valid answer.
Craft the pitch around THEIR evidence, in a tone fit for a luxury executive (no hype, no jargon).

## Output
JSON: {{
  "fit_score": int 0-100,
  "fit_rationale": str,
  "timing": str (why now / why not now),
  "the_problem": str (2-3 sentences, in their language),
  "opportunity_hypotheses": [{{"hypothesis": str, "evidence": str, "vestige_answer": str, "value": str}}],
  "pitch": {{"angle": str, "hook": str (first line of the conversation), "proof_points": [str],
            "entry_offer": str (a scoped first engagement), "objections": [{{"objection": str, "response": str}}]}},
  "decision_makers": [str] (roles to approach — no names),
  "outreach": {{"email_subject": str, "email_body": str (under 170 words, personal, references 1-2 public signals),
               "linkedin_note": str (under 300 characters), "follow_up": str}},
  "next_steps": [str]
}}
"""


def offer():
    return db.get_setting("vestige_offer", DEFAULT_OFFER)


def patterns():
    labels = {b["id"]: f"Maison {chr(65 + i % 26)}" for i, b in enumerate(db.query("SELECT id FROM brands ORDER BY id"))}
    runs = diagnostic.latest_per_brand()
    return "\n".join(diagnostic.summary_for_vestige(labels.get(d["brand_id"], "Maison"), d) for d in runs) \
        or "No completed diagnostics yet."


def radar(thesis, n=8, provider=None):
    existing = ", ".join(p["company"] for p in db.query("SELECT company FROM prospects")) or "none"
    data, model, sources, used_web = ai.research_json(
        RESEARCH_SYSTEM, RADAR_PROMPT.format(offer=offer(), thesis=thesis, existing=existing, n=n), provider)
    created = 0
    for c in data.get("candidates", []):
        if not c.get("company"):
            continue
        db.insert("prospects", {
            "company": c["company"][:200], "sector": c.get("sector", ""), "market": c.get("market", ""),
            "website": c.get("website", ""), "stage": "Suggested",
            "fit_score": max(0, min(100, int(c.get("fit_score") or 0))),
            "why": f"{c.get('signal', '')} — {c.get('why_vestige', '')}",
            "sources": [{"url": c["source_url"], "title": c.get("signal", "")[:80]}] if c.get("source_url") else [],
            "used_web": int(used_web), "model": model, "created_at": db.now(), "updated_at": db.now()})
        created += 1
    return created, model, used_web


def _set(pid, **values):
    values["updated_at"] = db.now()
    db.update("prospects", pid, values)


def run(pid, provider=None):
    p = db.query("SELECT * FROM prospects WHERE id = ?", (pid,), one=True)
    try:
        _set(pid, run_status="running", run_stage="research", error="")
        dossier, model, sources, used_web = ai.research_json(RESEARCH_SYSTEM, DOSSIER_PROMPT.format(
            company=p["company"], sector=p["sector"] or "unknown", market=p["market"] or "unknown",
            website=p["website"] or "unknown", material=p["material"] or "None."), provider)
        merged = {s["url"]: s for s in (p["sources"] or []) + sources}
        _set(pid, dossier=dossier, sources=list(merged.values()), used_web=int(used_web), run_stage="opportunity")
        pitch, model2 = ai.complete_json(VESTIGE_SYSTEM, OPPORTUNITY_PROMPT.format(
            offer=offer(), patterns=patterns(), company=p["company"],
            dossier=json.dumps(dossier, ensure_ascii=False)), provider)
        stage = "Researched" if p["stage"] in ("Suggested", "Identified") else p["stage"]
        _set(pid, pitch=pitch, fit_score=max(0, min(100, int(pitch.get("fit_score") or 0))), stage=stage,
             run_status="done", run_stage="done", model=", ".join(sorted({model, model2})))
    except ai.AIError as e:
        _set(pid, run_status="error", error=str(e))
    except Exception:
        current_app.logger.error(traceback.format_exc())
        _set(pid, run_status="error", error="Unexpected error — see server logs.")


def start(pid, provider=None):
    _set(pid, run_status="queued", run_stage="research")
    app = current_app._get_current_object()

    def worker():
        with app.app_context():
            run(pid, provider)

    if app.config.get("DIAGNOSTIC_SYNC"):
        worker()
    else:
        threading.Thread(target=worker, daemon=True).start()


def to_brand(p):
    """Won lead -> client engagement, pre-filled from the research."""
    d, pt = p["dossier"] or {}, p["pitch"] or {}
    snap = d.get("snapshot", {})
    brand_id = db.insert("brands", {
        "name": p["company"], "sector": p["sector"], "market": p["market"] or snap.get("markets", ""),
        "heritage": snap.get("heritage", ""), "positioning": snap.get("positioning", ""),
        "strategic_gaps": "\n".join(f"• {s.get('signal')}" for s in d.get("problem_signals", [])),
        "current_strategy": "Observed publicly before the engagement:\n" + "\n".join(
            f"• {i.get('initiative')} ({i.get('date', '')})" for i in d.get("initiatives", [])),
        "archetypes": "\n".join(f"{a.get('name')}: {a.get('rationale')}" for a in d.get("likely_archetypes", [])),
        "created_at": db.now(), "updated_at": db.now()})
    for c in d.get("competitors", []):
        if c.get("name"):
            db.insert("competitors", {"brand_id": brand_id, "name": c["name"], "actions": c.get("recent_actions", ""),
                                      "signals": c.get("source", ""), "created_at": db.now()})
    if pt.get("pitch", {}).get("entry_offer"):
        db.insert("items", {"brand_id": brand_id, "scope": "brand", "kind": "insight",
                            "title": "Entry engagement agreed in the pitch", "summary": pt["pitch"]["entry_offer"],
                            "status": "accepted", "model": "prospecting", "brand_label": p["company"],
                            "payload": {"category": "opportunity"}, "created_at": db.now(), "updated_at": db.now()})
    _set(p["id"], brand_id=brand_id, stage="Won")
    return brand_id
