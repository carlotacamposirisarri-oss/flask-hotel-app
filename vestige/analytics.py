"""Context builders for the AI and aggregate analytics for dashboards.

The internal intelligence and growth layers only see anonymised aggregates:
maisons become "Maison A/B/...", clients are never named.
"""
from collections import Counter, defaultdict

from . import db

AT_RISK = {"At risk", "Dormant"}
LOYAL = {"Loyal", "Ambassador"}


def _pct(part, whole):
    return round(100 * part / whole) if whole else 0


def _avg(values):
    values = [v for v in values if v is not None]
    return round(sum(values) / len(values), 1) if values else 0


# ------------------------------------------------------------------ brand ----

def brand_codes(brand):
    return f"""## Maison: {brand['name']}
Sector: {brand['sector']} · Market: {brand['market']}
Heritage narrative: {brand['heritage']}
Core values: {brand['core_values']}
Visual codes: {brand['visual_codes']}
Tone of voice: {brand['tone_of_voice']}
Client archetypes defined: {brand['archetypes']}
Market positioning: {brand['positioning']}
Known strategic gaps: {brand['strategic_gaps']}"""


def portfolio_stats(brand_id):
    clients = db.query("SELECT * FROM clients WHERE brand_id = ?", (brand_id,))
    n = len(clients)
    interests = Counter(i for c in clients for i in c["interests"])
    return {
        "clients": clients,
        "count": n,
        "avg_engagement": _avg([c["engagement_score"] for c in clients]),
        "total_ltv": sum(c["lifetime_value"] or 0 for c in clients),
        "at_risk": sum(c["phase"] in AT_RISK for c in clients),
        "loyal": sum(c["phase"] in LOYAL for c in clients),
        "phases": Counter(c["phase"] for c in clients).most_common(),
        "archetypes": Counter(c["archetype"] or "Unassigned" for c in clients).most_common(),
        "interests": interests.most_common(),
        "countries": Counter(c["country"] for c in clients if c["country"]).most_common(),
    }


def _client_line(c):
    return (f"- {c['name']} | {c['city']}, {c['country']} | tier {c['tier']} | {c['archetype']} | "
            f"phase {c['phase']} | engagement {c['engagement_score']} | LTV €{int(c['lifetime_value'] or 0):,} | "
            f"interests: {', '.join(c['interests'])} | signals: {(c['behavioral_signals'] or '')[:160]} | "
            f"cross-purchases: {(c['cross_purchases'] or '')[:120]}")


def brand_context(brand, competitors=False, max_clients=60):
    s = portfolio_stats(brand["id"])
    clients = sorted(s["clients"], key=lambda c: -(c["lifetime_value"] or 0))[:max_clients]
    parts = [brand_codes(brand), f"""
## Client portfolio ({s['count']} clients)
Average engagement: {s['avg_engagement']} · Loyal/Ambassador: {s['loyal']} · At risk/Dormant: {s['at_risk']}
Phases: {', '.join(f'{k} {v}' for k, v in s['phases'])}
Archetypes: {', '.join(f'{k} {v}' for k, v in s['archetypes'])}
Top interest clusters: {', '.join(f'{k} {v}' for k, v in s['interests'][:10])}
Countries: {', '.join(f'{k} {v}' for k, v in s['countries'][:10])}

### Clients (top {len(clients)} by lifetime value)
""" + "\n".join(_client_line(c) for c in clients)]
    if competitors:
        comps = db.query("SELECT * FROM competitors WHERE brand_id = ?", (brand["id"],))
        if comps:
            parts.append("## Competitors\n" + "\n".join(
                f"- {c['name']}: positioning {c['positioning']} | client tiers {c['client_tiers']} | "
                f"signals {c['signals']} | notes {c['notes']}" for c in comps))
    accepted = db.query(
        "SELECT kind, title FROM items WHERE brand_id = ? AND status = 'accepted' ORDER BY id DESC LIMIT 25",
        (brand["id"],))
    if accepted:
        parts.append("## Already accepted work (do not duplicate)\n" +
                     "\n".join(f"- [{a['kind']}] {a['title']}" for a in accepted))
    return "\n".join(parts)


# --------------------------------------------------------------- internal ----

def anonymised_brands():
    brands = db.query("SELECT * FROM brands ORDER BY id")
    return {b["id"]: f"Maison {chr(65 + i % 26)}{'' if i < 26 else i // 26}" for i, b in enumerate(brands)}, brands


def cross_brand():
    labels, brands = anonymised_brands()
    sector_of = {b["id"]: b["sector"] or "Unspecified" for b in brands}
    clients = db.query("SELECT brand_id, country, tier, archetype, phase, engagement_score, lifetime_value, "
                       "interests FROM clients")
    items = db.query("SELECT brand_id, kind, status, payload, urgency, impact FROM items WHERE scope = 'brand'")

    by_arch = defaultdict(list)
    for c in clients:
        by_arch[c["archetype"] or "Unassigned"].append(c)
    retention = sorted(
        [{"archetype": a, "clients": len(cs), "avg_engagement": _avg([c["engagement_score"] for c in cs]),
          "at_risk_pct": _pct(sum(c["phase"] in AT_RISK for c in cs), len(cs)),
          "loyal_pct": _pct(sum(c["phase"] in LOYAL for c in cs), len(cs))} for a, cs in by_arch.items()],
        key=lambda r: -r["clients"])

    sector_interests = defaultdict(Counter)
    for c in clients:
        sector_interests[sector_of.get(c["brand_id"], "Unspecified")].update(c["interests"])

    formats, collab_cats, audit_cats = Counter(), Counter(), Counter()
    format_impact = defaultdict(list)
    for it in items:
        p = it["payload"] or {}
        if it["kind"] == "initiative":
            fmt = str(p.get("format", "Other")).split("(")[0].strip()[:40] or "Other"
            formats[fmt] += 1
            try:
                format_impact[fmt].append(int(p.get("emotional_impact") or 0))
            except (TypeError, ValueError):
                pass
        elif it["kind"] == "collaboration":
            collab_cats[str(p.get("category", "Other"))[:40]] += 1
        elif it["kind"] == "audit":
            audit_cats[str(p.get("category", "Other"))[:40]] += 1

    benchmarks = []
    for b in brands:
        cs = [c for c in clients if c["brand_id"] == b["id"]]
        its = [i for i in items if i["brand_id"] == b["id"]]
        benchmarks.append({
            "label": labels[b["id"]], "sector": b["sector"] or "—", "clients": len(cs),
            "avg_engagement": _avg([c["engagement_score"] for c in cs]),
            "loyal_pct": _pct(sum(c["phase"] in LOYAL for c in cs), len(cs)),
            "at_risk_pct": _pct(sum(c["phase"] in AT_RISK for c in cs), len(cs)),
            "avg_ltv": round(_avg([c["lifetime_value"] for c in cs])),
            "initiatives": sum(i["kind"] == "initiative" for i in its),
            "acceptance_pct": _pct(sum(i["status"] == "accepted" for i in its),
                                   sum(i["status"] != "proposed" for i in its)),
        })

    return {
        "brands": len(brands), "clients": len(clients),
        "interests": Counter(i for c in clients for i in c["interests"]).most_common(),
        "sector_interests": {s: c.most_common(6) for s, c in sector_interests.items()},
        "retention": retention,
        "phases": Counter(c["phase"] for c in clients).most_common(),
        "countries": Counter(c["country"] for c in clients if c["country"]).most_common(12),
        "formats": [(f, n, _avg(format_impact[f])) for f, n in formats.most_common(10)],
        "collab_categories": collab_cats.most_common(10),
        "audit_categories": audit_cats.most_common(10),
        "benchmarks": benchmarks,
    }


def internal_context():
    x = cross_brand()
    fmt = lambda pairs: ", ".join(f"{k} {v}" for k, v in pairs)  # noqa: E731
    return f"""## Vestige cross-brand intelligence (anonymised)
{x['brands']} maisons · {x['clients']} clients tracked

Interest clusters (all clients): {fmt(x['interests'][:15])}
Interest clusters by sector:
""" + "\n".join(f"- {s}: {fmt(v)}" for s, v in x["sector_interests"].items()) + """

Retention by archetype:
""" + "\n".join(f"- {r['archetype']}: {r['clients']} clients, avg engagement {r['avg_engagement']}, "
                f"{r['loyal_pct']}% loyal/ambassador, {r['at_risk_pct']}% at risk/dormant" for r in x["retention"]) + f"""

Lifecycle phases: {fmt(x['phases'])}
Client geography: {fmt(x['countries'])}
Experiential formats proposed (count, avg emotional impact): """ + ", ".join(
        f"{f} {n} ({i})" for f, n, i in x["formats"]) + f"""
Collaboration categories: {fmt(x['collab_categories'])}
Recurring strategy weaknesses (audits): {fmt(x['audit_categories'])}

Benchmarks:
""" + "\n".join(f"- {b['label']} ({b['sector']}): {b['clients']} clients, engagement {b['avg_engagement']}, "
                f"{b['loyal_pct']}% loyal, {b['at_risk_pct']}% at risk, avg LTV €{b['avg_ltv']:,}"
                for b in x["benchmarks"])


# ------------------------------------------------------------ query builder ----

DIMENSIONS = {"archetype": "Archetype", "phase": "Lifecycle phase", "country": "Country", "tier": "Tier",
              "interest": "Interest cluster", "sector": "Maison sector"}
METRICS = {"clients": "Clients", "avg_engagement": "Avg engagement", "avg_ltv": "Avg lifetime value (€)",
           "at_risk_pct": "% at risk / dormant", "loyal_pct": "% loyal / ambassador"}


def run_query(dimension, metric, sector=""):
    _, brands = anonymised_brands()
    sector_of = {b["id"]: b["sector"] or "Unspecified" for b in brands}
    groups = defaultdict(list)
    for c in db.query("SELECT * FROM clients"):
        s = sector_of.get(c["brand_id"], "Unspecified")
        if sector and s != sector:
            continue
        if dimension == "interest":
            keys = c["interests"] or ["None"]
        elif dimension == "sector":
            keys = [s]
        else:
            keys = [c.get(dimension) or "Unspecified"]
        for k in keys:
            groups[k].append(c)
    rows = []
    for k, cs in groups.items():
        value = {
            "clients": len(cs),
            "avg_engagement": _avg([c["engagement_score"] for c in cs]),
            "avg_ltv": round(_avg([c["lifetime_value"] for c in cs])),
            "at_risk_pct": _pct(sum(c["phase"] in AT_RISK for c in cs), len(cs)),
            "loyal_pct": _pct(sum(c["phase"] in LOYAL for c in cs), len(cs)),
        }[metric]
        rows.append((k, value, len(cs)))
    return sorted(rows, key=lambda r: -r[1])


# ----------------------------------------------------------------- growth ----

def practice_kpis():
    status = Counter(r["status"] for r in db.query("SELECT status FROM items"))
    decided = status["accepted"] + status["dismissed"]
    return {
        "engagements": db.scalar("SELECT COUNT(*) FROM brands") or 0,
        "clients": db.scalar("SELECT COUNT(*) FROM clients") or 0,
        "deliverables": db.scalar("SELECT COUNT(*) FROM decks") or 0,
        "ai_items": sum(status.values()),
        "accepted": status["accepted"],
        "utilisation_pct": _pct(status["accepted"], decided),
        "competitors": db.scalar("SELECT COUNT(*) FROM competitors") or 0,
        "crm_rows": db.scalar("SELECT COALESCE(SUM(rows_imported), 0) FROM crm_imports") or 0,
    }


def growth_context():
    k = practice_kpis()
    labels, brands = anonymised_brands()
    kpis = db.query("SELECT * FROM kpis ORDER BY period DESC, id DESC LIMIT 40")
    goals = db.query("SELECT * FROM goals WHERE status = 'active'")
    kinds = Counter(r["kind"] for r in db.query("SELECT kind FROM items"))
    eng = []
    for b in brands:
        n_items = db.scalar("SELECT COUNT(*) FROM items WHERE brand_id = ?", (b["id"],))
        n_decks = db.scalar("SELECT COUNT(*) FROM decks WHERE brand_id = ?", (b["id"],))
        eng.append(f"- {labels[b['id']]}: sector {b['sector']}, market {b['market']}, started {b['created_at'][:10]}, "
                   f"{n_items} work items, {n_decks} deliverables, known gaps: {b['strategic_gaps'][:140]}")
    return f"""## Vestige practice data
Active engagements: {k['engagements']} · clients tracked {k['clients']} · deliverables {k['deliverables']}
AI work items {k['ai_items']} (accepted {k['accepted']}, utilisation {k['utilisation_pct']}%)
Work mix by type: {', '.join(f'{a} {b}' for a, b in kinds.most_common())}

### Engagements (anonymised)
""" + "\n".join(eng) + """

### Vestige KPIs (latest first)
""" + ("\n".join(f"- {r['period']} · {r['name']}: {r['value']:g} {r['unit']} {r['note']}" for r in kpis) or "none yet") + """

### Active growth goals
""" + ("\n".join(f"- {g['title']} — metric {g['metric']}: {g['current']:g} / {g['target']:g}, due {g['due']}. "
                 f"{g['notes']}" for g in goals) or "none yet") + "\n\n" + internal_context()


CONTEXT_BUILDERS = {
    "brand": lambda brand: brand_context(brand),
    "brand_competitors": lambda brand: brand_context(brand, competitors=True),
    "internal": lambda brand: internal_context(),
    "growth": lambda brand: growth_context(),
}
