"""The Vestige Engagement Diagnostic — the core pipeline of the service.

  1. Segmentation   (deterministic)  CRM behaviour -> behavioural segments
  2. Archetypes     (AI)             segments -> named, brand-relevant archetypes
  3. Cross-exam     (AI)             archetypes x brand identity x current strategy
                                     x competitor actions -> weaknesses & opportunities
  4. Strategy       (AI)             resource reallocation + experiential strategy
                                     maximising emotional impact and commercial results
Then the report page and the deck are rendered from the stored results.

Runs in a background thread; the report page shows live progress.
"""
import json
import threading
import traceback

from flask import current_app

from . import ai, analytics, db, segment
from .prompts import VESTIGE_SYSTEM

STAGES = [
    ("segmentation", "Reading CRM behaviour and detecting segments"),
    ("archetypes", "Naming archetypes through the maison's lens"),
    ("crossexam", "Cross-examining identity, current strategy and competitors"),
    ("strategy", "Designing reallocation and experiential strategy"),
]

ARCHETYPE_PROMPT = """{codes}

## Behavioural segments detected in the CRM ({n} clients, k={k}, silhouette {sil})
Segments were produced by clustering on interests, cross-industry purchases, own-brand categories,
lifetime value, purchase frequency, recency and engagement. "lift" = how much more common a trait is
in the segment than in the whole base (1.0 = average).

{segments}

{brief}
## Task
Interpret each segment as a client ARCHETYPE for this maison. Ground every statement in the
numbers above; when the data is thin, say so in data_caveats. Where a segment matches one of the
maison's existing archetypes, keep that name; otherwise coin an evocative, non-cliché name that
fits the maison's world.

## Output
JSON: {{"archetypes": [{{
  "segment_id": int,
  "name": str,
  "essence": str (one sentence),
  "defining_behaviours": [str] (3-5, each citing a number from the data),
  "motivations": [str],
  "emotional_drivers": [str],
  "relationship_to_brand": str,
  "commercial_role": str (why they matter to revenue: value share, growth or risk),
  "risk_signals": [str],
  "data_caveats": str
}}], "segmentation_reading": str (3-4 sentences on what the structure of the base reveals)}}
One entry per segment, same segment_id values.
"""

CROSSEXAM_PROMPT = """{codes}

## Current engagement & retention strategy (as described by the maison)
{strategy}

## Current resource allocation
{allocation}

## Competitors and their recent actions
{competitors}

## Archetypes (from the CRM)
{archetypes}

{brief}
## Task
Cross-examine the archetypes against (a) the brand identity, (b) the current engagement & retention
strategy and its resource allocation, and (c) the competitors' actions. Identify where effort and
money are misdirected, which archetypes are under-served or exposed to competitors, and where the
maison has a right to win. Be specific and candid; cite segment numbers.

## Output
JSON: {{
  "matrix": [{{"archetype": str, "segment_id": int,
              "identity_fit": int 0-100 (how naturally the brand's codes resonate with them),
              "strategy_coverage": int 0-100 (how well the current strategy serves them),
              "competitor_pressure": int 0-100,
              "main_competitor": str,
              "reading": str (one sentence)}}],
  "weaknesses": [{{"title": str, "evidence": str, "archetypes": [str],
                   "severity": "low|medium|high|critical", "cost_of_inaction": str}}],
  "opportunities": [{{"title": str, "evidence": str, "archetypes": [str],
                      "value_at_stake": str, "why_we_win": str}}],
  "competitor_reads": [{{"competitor": str, "what_they_do_well": str, "where_they_are_weak": str,
                         "archetypes_targeted": [str]}}],
  "synthesis": str (3-5 sentences: the core diagnosis)
}}
4-7 weaknesses and 4-7 opportunities, ranked by importance.
"""

STRATEGY_PROMPT = """{codes}

## Current resource allocation
{allocation}

## Archetypes
{archetypes}

## Diagnosis
{crossexam}

{brief}
## Task
Design the recommendation: redirect the maison's engagement & retention resources towards an
experiential strategy that maximises BOTH emotional impact on its VICs and commercial results.
Respect the brand codes; prefer fewer, deeper, ownable experiences over many generic ones.
Estimates must be reasoned from the segment numbers (value share, risk, size) — state assumptions.

## Output
JSON: {{
  "headline": str (the one-line strategic thesis),
  "executive_summary": [str] (5 key messages for the CEO),
  "north_star": {{"concept": str, "why_it_is_ownable": str}},
  "reallocation": [{{"from": str, "to": str, "shift_pct": int (share of total budget moved),
                     "rationale": str}}],
  "target_allocation": [{{"line": str, "pct": int}}] (sums to 100),
  "archetype_plays": [{{"archetype": str, "objective": str, "experiential_pillar": str,
                        "signature_experiences": [{{"name": str, "format": str, "description": str,
                                                    "emotional_impact": int 1-5, "commercial_kpi": str,
                                                    "expected_result": str}}],
                        "cadence": str}}],
  "roadmap": [{{"quarter": "Q1|Q2|Q3|Q4", "initiatives": [str]}}],
  "kpis": {{"emotional": [str], "commercial": [str]}},
  "quick_wins": [str] (first 90 days),
  "assumptions": [str]
}}
"""


def _segments_text(seg):
    out = []
    for s in seg["segments"]:
        fmt = lambda rows: ", ".join(f"{r['label']} {r['share']}% (lift {r['lift']})" for r in rows) or "—"  # noqa: E731
        out.append(
            f"### Segment {s['id']} — {s['size']} clients ({s['size_pct']}% of base), {s['value_pct']}% of value\n"
            f"avg LTV €{s['avg_ltv']:,} · avg purchases {s['avg_purchases']} · avg days since last purchase "
            f"{s['avg_recency_days']} · engagement {s['avg_engagement']} · loyal/ambassador {s['loyal_pct']}% · "
            f"at risk/dormant {s['at_risk_pct']}%\n"
            f"Interests: {fmt(s['interests'])}\nCross-industry purchases: {fmt(s['cross_industry'])}\n"
            f"Own-brand categories: {', '.join(c['label'] + ' ' + str(c['share']) + '%' for c in s['own_categories']) or '—'}\n"
            f"Countries: {', '.join(s['countries']) or '—'} · Labels used today: {s['prior_labels'] or '—'}\n"
            f"Behavioural notes: {' | '.join(x[:140] for x in s['signals'][:4]) or '—'}")
    return "\n\n".join(out)


def _archetypes_text(arch, seg):
    by_id = {s["id"]: s for s in seg["segments"]}
    rows = []
    for a in arch.get("archetypes", []):
        s = by_id.get(a.get("segment_id"), {})
        rows.append(f"- {a.get('name')} (segment {a.get('segment_id')}: {s.get('size_pct')}% of clients, "
                    f"{s.get('value_pct')}% of value, {s.get('at_risk_pct')}% at risk): {a.get('essence')} "
                    f"Behaviours: {'; '.join(a.get('defining_behaviours', []))}. "
                    f"Drivers: {', '.join(a.get('emotional_drivers', []))}.")
    return "\n".join(rows)


def _competitors_text(brand_id):
    comps = db.query("SELECT * FROM competitors WHERE brand_id = ?", (brand_id,))
    return "\n".join(f"- {c['name']}: positioning {c['positioning']} | tiers {c['client_tiers']} | "
                     f"signals {c['signals']} | recent actions {c['actions'] or 'not documented'}"
                     for c in comps) or "No competitors documented."


def _brief(diag):
    return f"## Brief from Vestige\n{diag['brief']}\n" if diag["brief"].strip() else ""


def _set(diag_id, **values):
    db.update("diagnostics", diag_id, values)


def run(diag_id, provider=None, apply_archetypes=True):
    diag = db.query("SELECT * FROM diagnostics WHERE id = ?", (diag_id,), one=True)
    brand = db.query("SELECT * FROM brands WHERE id = ?", (diag["brand_id"],), one=True)
    codes = analytics.brand_codes(brand)
    models = []
    try:
        _set(diag_id, status="running", stage="segmentation")
        clients = db.query("SELECT * FROM clients WHERE brand_id = ?", (brand["id"],))
        seg = segment.segment(clients)
        _set(diag_id, segmentation=seg, stage="archetypes")
        diag["segmentation"] = seg

        arch, m = ai.complete_json(VESTIGE_SYSTEM, ARCHETYPE_PROMPT.format(
            codes=codes, n=seg["quality"]["clients"], k=seg["quality"]["k"], sil=seg["quality"]["silhouette"],
            segments=_segments_text(seg), brief=_brief(diag)), provider)
        models.append(m)
        _set(diag_id, archetypes=arch, stage="crossexam")
        if apply_archetypes:
            names = {a.get("segment_id"): a.get("name") for a in arch.get("archetypes", [])}
            conn = db.get_db()
            for cid, sid in seg["assignments"].items():
                conn.execute("UPDATE clients SET segment = ?, archetype = COALESCE(?, archetype) WHERE id = ?",
                             (sid, names.get(sid), int(cid)))
            conn.commit()

        allocation = brand["resource_allocation"] or "Not provided — infer typical luxury allocation and flag it."
        cx, m = ai.complete_json(VESTIGE_SYSTEM, CROSSEXAM_PROMPT.format(
            codes=codes, strategy=brand["current_strategy"] or "Not documented — flag this as a gap.",
            allocation=allocation, competitors=_competitors_text(brand["id"]),
            archetypes=_archetypes_text(arch, seg), brief=_brief(diag)), provider)
        models.append(m)
        _set(diag_id, crossexam=cx, stage="strategy")

        st, m = ai.complete_json(VESTIGE_SYSTEM, STRATEGY_PROMPT.format(
            codes=codes, allocation=allocation, archetypes=_archetypes_text(arch, seg),
            crossexam=json.dumps(cx, ensure_ascii=False), brief=_brief(diag)), provider)
        models.append(m)
        _set(diag_id, strategy=st, status="done", stage="done", model=", ".join(sorted(set(models))),
             finished_at=db.now())
    except ValueError as e:
        _set(diag_id, status="error", error=str(e), finished_at=db.now())
    except ai.AIError as e:
        _set(diag_id, status="error", error=f"AI step failed: {e}", model=", ".join(models), finished_at=db.now())
    except Exception:  # keep the run inspectable instead of a silent dead thread
        current_app.logger.error(traceback.format_exc())
        _set(diag_id, status="error", error="Unexpected error — see server logs.", finished_at=db.now())


def start(brand_id, brief="", provider=None):
    diag_id = db.insert("diagnostics", {"brand_id": brand_id, "brief": brief, "status": "queued",
                                        "created_at": db.now()})
    app = current_app._get_current_object()

    def worker():
        with app.app_context():
            run(diag_id, provider)

    if app.config.get("DIAGNOSTIC_SYNC"):  # tests
        worker()
    else:
        threading.Thread(target=worker, daemon=True).start()
    return diag_id


def summary_for_vestige(label, diag):
    """Anonymised digest of one diagnostic, for the Vestige intelligence and growth layers."""
    seg = diag["segmentation"] or {}
    by_id = {s["id"]: s for s in seg.get("segments", [])}
    arch = [f"{a.get('name')} ({by_id.get(a.get('segment_id'), {}).get('size_pct', '?')}% clients, "
            f"{by_id.get(a.get('segment_id'), {}).get('value_pct', '?')}% value, "
            f"{by_id.get(a.get('segment_id'), {}).get('at_risk_pct', '?')}% at risk)"
            for a in (diag["archetypes"] or {}).get("archetypes", [])]
    cx = diag["crossexam"] or {}
    st = diag["strategy"] or {}
    return (f"- {label}: archetypes {'; '.join(arch) or 'n/a'}.\n"
            f"  Weaknesses: {'; '.join(w.get('title', '') + ' [' + w.get('severity', '') + ']' for w in cx.get('weaknesses', []))}.\n"
            f"  Opportunities: {'; '.join(o.get('title', '') for o in cx.get('opportunities', []))}.\n"
            f"  Reallocation: {'; '.join(r.get('from', '') + ' -> ' + r.get('to', '') + ' (' + str(r.get('shift_pct', '')) + '%)' for r in st.get('reallocation', []))}.\n"
            f"  Thesis: {st.get('headline', '')}")


def latest_per_brand():
    return db.query("SELECT d.* FROM diagnostics d JOIN (SELECT brand_id, MAX(id) AS id FROM diagnostics "
                    "WHERE status = 'done' GROUP BY brand_id) last ON last.id = d.id")
