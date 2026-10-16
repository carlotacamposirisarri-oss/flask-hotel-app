"""All routes. Pages are server-rendered; AI generation is synchronous POST."""
import json
import re
from datetime import date

from flask import (Blueprint, Response, abort, flash, jsonify, redirect, render_template, request,
                   send_file, url_for)

from . import ai, analytics, crm, db, decks, diagnostic, prospecting
from .prompts import (CLIENT_GAPS_PROMPT, DEFAULT_ARCHETYPES, DISCOVERY_PROMPT, INTEREST_CLUSTERS, KINDS,
                      PHASES, VESTIGE_SYSTEM, item_prompt)

bp = Blueprint("v", __name__)

BRAND_FIELDS = ["name", "sector", "market", "heritage", "core_values", "visual_codes", "tone_of_voice",
                "archetypes", "positioning", "strategic_gaps", "accent_color", "current_strategy",
                "resource_allocation"]
CLIENT_FIELDS = ["name", "email", "country", "city", "tier", "archetype", "phase", "social_footprint",
                 "cross_purchases", "behavioral_signals", "info_gaps", "notes"]


# ---------------------------------------------------------------- helpers ----

def get_brand(brand_id):
    brand = db.query("SELECT * FROM brands WHERE id = ?", (brand_id,), one=True)
    if not brand:
        abort(404)
    return brand


def brand_archetypes(brand):
    names = [a.split(":")[0].strip() for a in re.split(r"[\n;]", brand["archetypes"] or "") if a.strip()]
    return names or DEFAULT_ARCHETYPES


def items_of(kinds, brand_id=None, scope=None, include_dismissed=False):
    kinds = [kinds] if isinstance(kinds, str) else kinds
    sql = f"SELECT * FROM items WHERE kind IN ({','.join('?' for _ in kinds)})"
    args = list(kinds)
    if brand_id is not None:
        sql += " AND brand_id = ?"
        args.append(brand_id)
    if scope:
        sql += " AND scope = ?"
        args.append(scope)
    if not include_dismissed:
        sql += " AND status != 'dismissed'"
    sql += " ORDER BY (status = 'accepted') DESC, priority DESC, urgency * impact DESC, id DESC"
    return db.query(sql, args)


def grouped(kinds, brand_id=None, scope=None):
    show_dismissed = request.args.get("dismissed") == "1"
    return {k: items_of(k, brand_id, scope, show_dismissed) for k in kinds}


def back(default="/"):
    nxt = request.form.get("next") or request.args.get("next") or ""
    return redirect(nxt if nxt.startswith("/") and not nxt.startswith("//") else default)


def _int(v, default=0, lo=None, hi=None):
    try:
        v = int(float(v))
    except (TypeError, ValueError):
        v = default
    if lo is not None:
        v = max(lo, v)
    if hi is not None:
        v = min(hi, v)
    return v


def _float(v, default=0.0):
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return default


def _split(v):
    return [x.strip() for x in re.split(r"[,\n]", v or "") if x.strip()]


# ------------------------------------------------------------- dashboard ----

@bp.route("/")
def dashboard():
    brands = db.query("SELECT * FROM brands ORDER BY updated_at DESC")
    cards = []
    for b in brands:
        s = analytics.portfolio_stats(b["id"])
        cards.append({**b, "stats": s, "open_items": db.scalar(
            "SELECT COUNT(*) FROM items WHERE brand_id = ? AND status = 'proposed'", (b["id"],))})
    top = db.query("SELECT items.*, brands.name AS brand_name FROM items LEFT JOIN brands ON brands.id = items.brand_id "
                   "WHERE kind = 'insight' AND status = 'proposed' ORDER BY urgency * impact DESC, id DESC LIMIT 6")
    return render_template("dashboard.html", cards=cards, top=top, kpis=analytics.practice_kpis())


# -------------------------------------------------------------- settings ----

@bp.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        f = request.form
        for name in ai.SECRET_KEYS:
            if f.get(f"clear_{name}"):
                ai.save_secret(name, "")
            elif f.get(name, "").strip():
                ai.save_secret(name, f[name])
        db.set_setting("ai_primary", f.get("primary", "claude"))
        db.set_setting("ai_fallback", "on" if f.get("fallback") else "off")
        if f.get("claude_model") in ai.CLAUDE_MODELS:
            db.set_setting("claude_model", f["claude_model"])
        if f.get("claude_effort") in ("low", "medium", "high", "xhigh", "max"):
            db.set_setting("claude_effort", f["claude_effort"])
        db.set_setting("astra_base_url", f.get("astra_base_url", "").strip())
        db.set_setting("astra_model", f.get("astra_model", "").strip())
        if f.get("vestige_offer", "").strip():
            db.set_setting("vestige_offer", f["vestige_offer"].strip())
        flash("Settings saved. Keys are stored server-side only.", "ok")
        return redirect(url_for("v.settings"))
    return render_template("settings.html", models=ai.CLAUDE_MODELS, offer=prospecting.offer())


@bp.post("/settings/test")
def settings_test():
    provider = request.form.get("provider", "claude")
    try:
        text, model = ai.complete("Reply with one word.", "Say: connected", provider=provider, max_tokens=2000)
        flash(f"{model} responded: {text.strip()[:60]}", "ok")
    except ai.AIError as e:
        flash(str(e), "error")
    return redirect(url_for("v.settings"))


# ---------------------------------------------------------------- brands ----

@bp.route("/brands/new", methods=["GET", "POST"])
@bp.route("/b/<int:brand_id>/edit", methods=["GET", "POST"])
def brand_form(brand_id=None):
    brand = get_brand(brand_id) if brand_id else None
    if request.method == "POST":
        values = {k: request.form.get(k, "").strip() for k in BRAND_FIELDS}
        if not values["name"]:
            flash("The maison needs a name.", "error")
            return render_template("brand_form.html", brand=values)
        values["updated_at"] = db.now()
        if brand:
            db.update("brands", brand_id, values)
        else:
            values["created_at"] = db.now()
            brand_id = db.insert("brands", values)
        flash("Engagement saved.", "ok")
        return redirect(url_for("v.brand", brand_id=brand_id))
    return render_template("brand_form.html", brand=brand or {"accent_color": "#8C6A4A"},
                           default_archetypes=DEFAULT_ARCHETYPES)


@bp.post("/b/<int:brand_id>/delete")
def brand_delete(brand_id):
    get_brand(brand_id)
    db.delete("brands", brand_id)
    flash("Engagement deleted.", "ok")
    return redirect(url_for("v.dashboard"))


@bp.route("/b/<int:brand_id>")
def brand(brand_id):
    b = get_brand(brand_id)
    s = analytics.portfolio_stats(brand_id)
    counts = {k: db.scalar("SELECT COUNT(*) FROM items WHERE brand_id = ? AND kind = ? AND status != 'dismissed'",
                           (brand_id, k)) for k in KINDS}
    insights = items_of("insight", brand_id)[:4]
    return render_template("brand.html", brand=b, stats=s, counts=counts, insights=insights,
                           decks=db.query("SELECT * FROM decks WHERE brand_id = ? ORDER BY id DESC", (brand_id,)))


# --------------------------------------------------------------- clients ----

@bp.route("/b/<int:brand_id>/clients")
def clients(brand_id):
    b = get_brand(brand_id)
    q = request.args.get("q", "").strip().lower()
    phase, arch, interest = (request.args.get(k, "") for k in ("phase", "archetype", "interest"))
    rows = db.query("SELECT * FROM clients WHERE brand_id = ? ORDER BY engagement_score DESC", (brand_id,))
    if q:
        rows = [c for c in rows if q in (c["name"] + c["city"] + c["country"] + c["notes"]).lower()]
    if phase:
        rows = [c for c in rows if c["phase"] == phase]
    if arch:
        rows = [c for c in rows if c["archetype"] == arch]
    if interest:
        rows = [c for c in rows if interest in c["interests"]]
    return render_template("clients.html", brand=b, clients=rows, phases=PHASES, archetypes=brand_archetypes(b),
                           clusters=INTEREST_CLUSTERS, stats=analytics.portfolio_stats(brand_id))


def _client_values(form):
    v = {k: form.get(k, "").strip() for k in CLIENT_FIELDS}
    v["phase"] = v["phase"] or "Discovery"
    v["engagement_score"] = _int(form.get("engagement_score"), 50, 0, 100)
    v["lifetime_value"] = _float(form.get("lifetime_value"))
    v["interests"] = form.getlist("interests") or _split(form.get("interests_text"))
    affinities = {}
    for cluster in v["interests"]:
        affinities[cluster] = _int(form.get(f"aff_{cluster}"), 60, 0, 100)
    v["affinities"] = affinities
    v["social_circle"] = _split(form.get("social_circle"))
    v["updated_at"] = db.now()
    return v


@bp.route("/b/<int:brand_id>/clients/new", methods=["GET", "POST"])
@bp.route("/b/<int:brand_id>/clients/<int:client_id>/edit", methods=["GET", "POST"])
def client_form(brand_id, client_id=None):
    b = get_brand(brand_id)
    client = db.query("SELECT * FROM clients WHERE id = ? AND brand_id = ?", (client_id, brand_id), one=True) \
        if client_id else None
    if client_id and not client:
        abort(404)
    if request.method == "POST":
        values = _client_values(request.form)
        if not values["name"]:
            flash("Name is required.", "error")
            return redirect(request.path)
        if client:
            db.update("clients", client_id, values)
        else:
            values.update(brand_id=brand_id, created_at=db.now(), source=request.form.get("source", "manual"))
            client_id = db.insert("clients", values)
            db.insert("client_events", {"client_id": client_id, "date": date.today().isoformat(),
                                        "kind": "Profile created", "description": f"Source: {values['source']}"})
        db.update("brands", brand_id, {"updated_at": db.now()})
        flash("Client profile saved.", "ok")
        return redirect(url_for("v.client", brand_id=brand_id, client_id=client_id))
    return render_template("client_form.html", brand=b, client=client or {"interests": [], "affinities": {},
                           "social_circle": [], "phase": "Discovery", "engagement_score": 50},
                           phases=PHASES, archetypes=brand_archetypes(b), clusters=INTEREST_CLUSTERS)


@bp.route("/b/<int:brand_id>/clients/<int:client_id>")
def client(brand_id, client_id):
    b = get_brand(brand_id)
    c = db.query("SELECT * FROM clients WHERE id = ? AND brand_id = ?", (client_id, brand_id), one=True)
    if not c:
        abort(404)
    events = db.query("SELECT * FROM client_events WHERE client_id = ? ORDER BY date DESC, id DESC", (client_id,))
    peers = db.query("SELECT id, name, interests, archetype FROM clients WHERE brand_id = ? AND id != ?",
                     (brand_id, client_id))
    graph = {"nodes": [{"id": "c", "label": c["name"], "group": "client", "size": 26}], "links": []}
    for cluster in c["interests"]:
        graph["nodes"].append({"id": "i:" + cluster, "label": cluster, "group": "interest",
                               "size": 8 + c["affinities"].get(cluster, 50) / 8})
        graph["links"].append({"source": "c", "target": "i:" + cluster, "kind": "passion"})
    for person in c["social_circle"]:
        graph["nodes"].append({"id": "s:" + person, "label": person, "group": "circle", "size": 9})
        graph["links"].append({"source": "c", "target": "s:" + person, "kind": "circle"})
    for purchase in _split(c["cross_purchases"])[:6]:
        graph["nodes"].append({"id": "p:" + purchase, "label": purchase[:28], "group": "purchase", "size": 8})
        graph["links"].append({"source": "c", "target": "p:" + purchase, "kind": "purchase"})
    shared_peers = sorted(((p, set(p["interests"]) & set(c["interests"])) for p in peers),
                          key=lambda t: -len(t[1]))[:6]
    for p, shared in shared_peers:
        if not shared:
            continue
        pid = f"k:{p['id']}"
        graph["nodes"].append({"id": pid, "label": p["name"], "group": "peer", "size": 10,
                               "href": url_for("v.client", brand_id=brand_id, client_id=p["id"])})
        for s in shared:
            graph["links"].append({"source": pid, "target": "i:" + s, "kind": "shared"})
    return render_template("client.html", brand=b, c=c, events=events, graph=graph,
                           peers=[(p, s) for p, s in shared_peers if s])


@bp.post("/b/<int:brand_id>/clients/<int:client_id>/event")
def client_event(brand_id, client_id):
    get_brand(brand_id)
    db.insert("client_events", {"client_id": client_id, "date": request.form.get("date") or date.today().isoformat(),
                                "kind": request.form.get("kind", "Note"),
                                "description": request.form.get("description", "")})
    return redirect(url_for("v.client", brand_id=brand_id, client_id=client_id))


@bp.post("/b/<int:brand_id>/clients/<int:client_id>/delete")
def client_delete(brand_id, client_id):
    get_brand(brand_id)
    db.get_db().execute("DELETE FROM clients WHERE id = ? AND brand_id = ?", (client_id, brand_id))
    db.get_db().commit()
    flash("Client removed.", "ok")
    return redirect(url_for("v.clients", brand_id=brand_id))


@bp.post("/b/<int:brand_id>/clients/<int:client_id>/ai")
def client_ai(brand_id, client_id):
    b = get_brand(brand_id)
    c = db.query("SELECT * FROM clients WHERE id = ? AND brand_id = ?", (client_id, brand_id), one=True)
    if not c:
        abort(404)
    profile = {k: c[k] for k in CLIENT_FIELDS + ["interests", "affinities", "social_circle", "engagement_score",
                                                  "lifetime_value"]}
    try:
        data, model = ai.complete_json(VESTIGE_SYSTEM, CLIENT_GAPS_PROMPT.format(
            context=analytics.brand_codes(b), client=json.dumps(profile, ensure_ascii=False)),
            request.form.get("provider"))
    except ai.AIError as e:
        flash(str(e), "error")
        return redirect(url_for("v.client", brand_id=brand_id, client_id=client_id))
    gaps = data.get("info_gaps") or []
    db.update("clients", client_id, {"info_gaps": "\n".join(f"• {g}" for g in gaps), "updated_at": db.now()})
    patterns = "; ".join(data.get("patterns") or [])
    db.insert("client_events", {"client_id": client_id, "date": date.today().isoformat(), "kind": f"AI · {model}",
                                "description": f"Next best action: {data.get('next_best_action', '')}"
                                               f"{' — Patterns: ' + patterns if patterns else ''}"})
    flash("AI review added to the timeline and info gaps.", "ok")
    return redirect(url_for("v.client", brand_id=brand_id, client_id=client_id))


@bp.route("/b/<int:brand_id>/discovery", methods=["GET", "POST"])
def discovery(brand_id):
    b = get_brand(brand_id)
    draft, model = None, None
    if request.method == "POST":
        notes = request.form.get("notes", "")
        try:
            draft, model = ai.complete_json(VESTIGE_SYSTEM, DISCOVERY_PROMPT.format(
                context=analytics.brand_codes(b), notes=notes, clusters=", ".join(INTEREST_CLUSTERS),
                phases=", ".join(PHASES), archetypes=", ".join(brand_archetypes(b))), request.form.get("provider"))
            draft.setdefault("interests", [])
            draft.setdefault("affinities", {})
            draft.setdefault("social_circle", [])
            if isinstance(draft.get("info_gaps"), list):
                draft["info_gaps"] = "\n".join(f"• {g}" for g in draft["info_gaps"])
        except ai.AIError as e:
            flash(str(e), "error")
        return render_template("discovery.html", brand=b, draft=draft, model=model, notes=notes,
                               phases=PHASES, archetypes=brand_archetypes(b), clusters=INTEREST_CLUSTERS)
    return render_template("discovery.html", brand=b, draft=None, notes="", phases=PHASES,
                           archetypes=brand_archetypes(b), clusters=INTEREST_CLUSTERS)


# ------------------------------------------------------------------- CRM ----

@bp.route("/b/<int:brand_id>/crm", methods=["GET", "POST"])
def crm_import(brand_id):
    b = get_brand(brand_id)
    if request.method == "POST":
        token = request.form.get("token")
        if token:  # step 2: confirm mapping and ingest
            stash = crm.load_stash(token)
            if not stash:
                flash("Upload expired — please upload the file again.", "error")
                return redirect(request.path)
            mapping = {h: request.form.get(f"map_{i}", "") for i, h in enumerate(stash["headers"])}
            if stash.get("kind") == "transactions":
                if not any(v in ("name", "first_name", "last_name", "email", "client_ref") for v in mapping.values()) \
                        or "amount" not in mapping.values():
                    flash("Map a client identifier and the amount column.", "error")
                    return render_template("crm.html", brand=b, stash=stash, token=token, mapping=mapping,
                                           fields=crm.TX_FIELDS, logs=[])
                n_clients, n_rows = crm.ingest_transactions(brand_id, stash["rows"], mapping)
                db.insert("crm_imports", {"brand_id": brand_id, "filename": stash["filename"] + " (transactions)",
                                          "source_system": request.form.get("source_system", ""),
                                          "rows_total": len(stash["rows"]), "rows_imported": n_rows,
                                          "mapping": mapping, "created_at": db.now()})
                crm.drop_stash(token)
                flash(f"Aggregated {n_rows} purchases into the history of {n_clients} clients.", "ok")
                return redirect(url_for("v.clients", brand_id=brand_id))
            if not any(v in ("name", "first_name", "last_name") for v in mapping.values()):
                flash("Map at least one column to a name field.", "error")
                return render_template("crm.html", brand=b, stash=stash, token=token, mapping=mapping,
                                       fields=crm.FIELDS, logs=[])
            n = crm.ingest(brand_id, stash["rows"], mapping)
            db.insert("crm_imports", {"brand_id": brand_id, "filename": stash["filename"],
                                      "source_system": request.form.get("source_system", ""),
                                      "rows_total": len(stash["rows"]), "rows_imported": n,
                                      "mapping": mapping, "created_at": db.now()})
            crm.drop_stash(token)
            db.update("brands", brand_id, {"updated_at": db.now()})
            flash(f"Imported {n} of {len(stash['rows'])} rows into client profiles.", "ok")
            return redirect(url_for("v.clients", brand_id=brand_id))
        f = request.files.get("file")
        if not f or not f.filename:
            flash("Choose a CSV or Excel file.", "error")
            return redirect(request.path)
        try:
            headers, rows = crm.parse_upload(f)
        except Exception:  # malformed spreadsheet
            flash("Could not read that file. Export as CSV (UTF-8) or .xlsx and retry.", "error")
            return redirect(request.path)
        if not headers or not rows:
            flash("The file has no data rows.", "error")
            return redirect(request.path)
        kind = "transactions" if request.form.get("kind") == "transactions" else "clients"
        token = crm.stash(headers, rows, f.filename, kind)
        return render_template("crm.html", brand=b, stash={"headers": headers, "rows": rows, "filename": f.filename,
                                                           "kind": kind},
                               token=token, mapping=crm.auto_map_tx(headers) if kind == "transactions" else crm.auto_map(headers),
                               fields=crm.TX_FIELDS if kind == "transactions" else crm.FIELDS, logs=[],
                               source_system=request.form.get("source_system", ""))
    logs = db.query("SELECT * FROM crm_imports WHERE brand_id = ? ORDER BY id DESC", (brand_id,))
    return render_template("crm.html", brand=b, stash=None, logs=logs, fields=crm.FIELDS)


@bp.route("/crm-template.csv")
def crm_template():
    header = "Full name,Email,Country,City,Tier,Lifecycle stage,Engagement score,Total spend,Interests,Last activity,Notes\n"
    sample = ('Jane Example,jane@example.com,France,Paris,Platinum,Customer,72,"185000","Arts, Sailing, Wine",'
              'Visited atelier 2026-09,Prefers private appointments\n')
    return Response(header + sample, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=vestige-crm-template.csv"})


# ----------------------------------------------------------- competitors ----

@bp.route("/b/<int:brand_id>/competitors", methods=["GET", "POST"])
def competitors(brand_id):
    b = get_brand(brand_id)
    if request.method == "POST":
        f = request.form
        if f.get("action") == "axes":
            db.update("brands", brand_id, {"map_x_label": f.get("map_x_label", ""), "map_y_label": f.get("map_y_label", ""),
                                           "map_x": _int(f.get("map_x"), 50, 0, 100), "map_y": _int(f.get("map_y"), 50, 0, 100)})
        else:
            values = {k: f.get(k, "").strip() for k in ("name", "positioning", "client_tiers", "signals", "actions", "notes")}
            values.update(axis_x=_int(f.get("axis_x"), 50, 0, 100), axis_y=_int(f.get("axis_y"), 50, 0, 100))
            if f.get("id"):
                db.get_db().execute("UPDATE competitors SET name=?, positioning=?, client_tiers=?, signals=?, actions=?, "
                                    "notes=?, axis_x=?, axis_y=? WHERE id=? AND brand_id=?",
                                    (*[values[k] for k in ("name", "positioning", "client_tiers", "signals", "actions",
                                                           "notes", "axis_x", "axis_y")], f["id"], brand_id))
                db.get_db().commit()
            elif values["name"]:
                db.insert("competitors", {**values, "brand_id": brand_id, "created_at": db.now()})
        return redirect(url_for("v.competitors", brand_id=brand_id))
    comps = db.query("SELECT * FROM competitors WHERE brand_id = ? ORDER BY name", (brand_id,))
    return render_template("competitors.html", brand=b, comps=comps, groups=grouped(["competitive"], brand_id),
                           edit=next((c for c in comps if str(c["id"]) == request.args.get("edit")), None))


@bp.post("/b/<int:brand_id>/competitors/<int:comp_id>/delete")
def competitor_delete(brand_id, comp_id):
    db.get_db().execute("DELETE FROM competitors WHERE id = ? AND brand_id = ?", (comp_id, brand_id))
    db.get_db().commit()
    return redirect(url_for("v.competitors", brand_id=brand_id))


# --------------------------------------------------- generic work sections ----

SECTION_PAGES = {
    "insights": ("Insight Feed & Analyst", ["insight", "prospect"],
                 "A living stream of observations, opportunities and risks — and an analyst on call for your questions."),
    "studio": ("Storytelling & Community Studio", ["story", "community"],
               "Narrative strategies and community blueprints, written through the maison's codes."),
    "retention": ("Retention & Experiential Planner", ["retention", "initiative"],
                  "Archetype-led retention plays and a living twelve-month roadmap of experiences."),
    "collaborations": ("Cross-Industry Collaborations", ["collaboration"],
                       "Partnership pipeline scored for compatibility and checked for brand fit."),
    "emotion": ("Emotional Connection & Strategy Audit", ["cx_map", "event_design", "audit"],
                "Journey touchpoints, emotional event design and an honest audit of the current strategy."),
}


@bp.route("/b/<int:brand_id>/<section>")
def section(brand_id, section):
    if section not in SECTION_PAGES:
        abort(404)
    b = get_brand(brand_id)
    title, kinds, lede = SECTION_PAGES[section]
    groups = grouped(kinds, brand_id)
    timeline = None
    if section == "retention":
        timeline = {m: [i for i in groups["initiative"] if i["month"] == m] for m in range(1, 13)}
    return render_template("section.html", brand=b, section=section, title=title, lede=lede, groups=groups,
                           timeline=timeline, stats=analytics.portfolio_stats(brand_id))


# ------------------------------------------------------------ generation ----

@bp.post("/generate/<kind>")
def generate(kind):
    spec = KINDS.get(kind) or abort(404)
    brand_id = request.form.get("brand_id", type=int)
    brand = get_brand(brand_id) if brand_id else None
    if spec["scope"] == "brand" and not brand:
        abort(400)
    extra = request.form.get("extra", "")
    if spec.get("input_required") and not extra.strip():
        flash("Add a brief first.", "error")
        return back()
    context = analytics.CONTEXT_BUILDERS[spec["context"]](brand)
    system = VESTIGE_SYSTEM
    try:
        data, model = ai.complete_json(system, item_prompt(kind, context, extra), request.form.get("provider"))
    except ai.AIError as e:
        flash(str(e), "error")
        return back()
    raw = data.get("items", data) if isinstance(data, dict) else data
    raw = raw if isinstance(raw, list) else [raw]
    created = 0
    for it in raw:
        if not isinstance(it, dict) or not it.get("title"):
            continue
        payload = {k: it[k] for k in spec["fields"] if k in it and k != "month"}
        db.insert("items", {
            "brand_id": brand_id if spec["scope"] == "brand" else None, "scope": spec["scope"], "kind": kind,
            "title": str(it["title"])[:200], "summary": str(it.get("summary", "")),
            "payload": payload, "urgency": _int(it.get("urgency"), 3, 1, 5), "impact": _int(it.get("impact"), 3, 1, 5),
            "month": _int(it.get("month"), 0, 1, 12) if spec.get("uses_month") else None,
            "model": model, "brand_label": brand["name"] if brand else "Vestige internal",
            "prompt": extra[:2000], "created_at": db.now(), "updated_at": db.now(),
        })
        created += 1
    if brand:
        db.update("brands", brand_id, {"updated_at": db.now()})
    flash(f"{created} new {spec['plural'].lower()} item(s) from {model}. Review, refine or dismiss.", "ok")
    return back()


@bp.post("/items/new")
def item_new():
    kind = request.form.get("kind")
    spec = KINDS.get(kind) or abort(400)
    brand_id = request.form.get("brand_id", type=int)
    brand = get_brand(brand_id) if brand_id else None
    title = request.form.get("title", "").strip()
    if not title:
        flash("A title is required.", "error")
        return back()
    db.insert("items", {"brand_id": brand_id if spec["scope"] == "brand" else None, "scope": spec["scope"],
                        "kind": kind, "title": title, "summary": request.form.get("summary", ""),
                        "payload": {}, "status": "accepted", "model": "manual",
                        "month": _int(request.form.get("month"), 0, 1, 12) if spec.get("uses_month") else None,
                        "brand_label": brand["name"] if brand else "Vestige internal",
                        "created_at": db.now(), "updated_at": db.now()})
    return back()


@bp.post("/items/<int:item_id>")
def item_update(item_id):
    item = db.query("SELECT * FROM items WHERE id = ?", (item_id,), one=True) or abort(404)
    action = request.form.get("action")
    values = {"updated_at": db.now()}
    if action in ("accept", "dismiss", "restore"):
        values["status"] = {"accept": "accepted", "dismiss": "dismissed", "restore": "proposed"}[action]
    elif action == "delete":
        db.delete("items", item_id)
        return jsonify(ok=True) if request.accept_mimetypes.best == "application/json" else back()
    elif action == "edit":
        values.update(title=request.form.get("title", item["title"])[:200],
                      summary=request.form.get("summary", item["summary"]),
                      annotation=request.form.get("annotation", item["annotation"]))
        if "month" in request.form:
            values["month"] = _int(request.form.get("month"), 0, 1, 12) or None
        if "priority" in request.form:
            values["priority"] = _int(request.form.get("priority"), 0, 0, 10)
    elif action == "star":
        values["priority"] = 0 if item["priority"] else 5
    db.update("items", item_id, values)
    if request.accept_mimetypes.best == "application/json":
        return jsonify(ok=True, **values)
    return back()


# ----------------------------------------------------------- intelligence ----

@bp.route("/intelligence", methods=["GET", "POST"])
def intelligence():
    if request.method == "POST":
        if request.form.get("action") == "delete_query":
            db.delete("saved_queries", _int(request.form.get("id")))
        else:
            db.insert("saved_queries", {"name": request.form.get("name") or "Untitled query",
                                        "dimension": request.form.get("dimension"), "metric": request.form.get("metric"),
                                        "sector": request.form.get("sector", ""), "created_at": db.now()})
            flash("Query saved.", "ok")
        return redirect(url_for("v.intelligence", **{k: request.form.get(k, "") for k in ("dimension", "metric", "sector")}))
    dim = request.args.get("dimension") or "archetype"
    metric = request.args.get("metric") or "avg_engagement"
    sector = request.args.get("sector", "")
    dim = dim if dim in analytics.DIMENSIONS else "archetype"
    metric = metric if metric in analytics.METRICS else "avg_engagement"
    sectors = sorted({b["sector"] for b in db.query("SELECT sector FROM brands") if b["sector"]})
    labels, _ = analytics.anonymised_brands()
    library = []
    for d in diagnostic.latest_per_brand():
        by_id = {sg["id"]: sg for sg in d["segmentation"].get("segments", [])}
        for a in d["archetypes"].get("archetypes", []):
            sg = by_id.get(a.get("segment_id"), {})
            library.append({"maison": labels.get(d["brand_id"], "Maison"), "name": a.get("name"), "essence": a.get("essence"),
                            "size_pct": sg.get("size_pct"), "value_pct": sg.get("value_pct"), "at_risk_pct": sg.get("at_risk_pct"),
                            "interests": ", ".join(r["label"] for r in sg.get("interests", [])[:3])})
    return render_template("intelligence.html", x=analytics.cross_brand(), library=library, groups=grouped(["brief"], scope="internal"),
                           dims=analytics.DIMENSIONS, metrics=analytics.METRICS, sectors=sectors,
                           q={"dimension": dim, "metric": metric, "sector": sector},
                           results=analytics.run_query(dim, metric, sector),
                           saved=db.query("SELECT * FROM saved_queries ORDER BY id DESC"))


# ---------------------------------------------------------------- growth ----

@bp.route("/growth", methods=["GET", "POST"])
def growth():
    if request.method == "POST":
        f = request.form
        act = f.get("action")
        if act == "kpi":
            db.insert("kpis", {"period": f.get("period") or date.today().strftime("%Y-%m"), "name": f.get("name", ""),
                               "value": _float(f.get("value")), "unit": f.get("unit", ""), "note": f.get("note", ""),
                               "created_at": db.now()})
        elif act == "kpi_delete":
            db.delete("kpis", _int(f.get("id")))
        elif act == "goal":
            db.insert("goals", {"title": f.get("title", ""), "metric": f.get("metric", ""),
                                "target": _float(f.get("target")), "current": _float(f.get("current")),
                                "due": f.get("due", ""), "notes": f.get("notes", ""), "created_at": db.now(),
                                "updated_at": db.now()})
        elif act == "goal_update":
            db.update("goals", _int(f.get("id")), {"current": _float(f.get("current")),
                                                   "status": f.get("status", "active"), "updated_at": db.now()})
        elif act == "goal_delete":
            db.delete("goals", _int(f.get("id")))
        return redirect(url_for("v.growth"))
    kpis = db.query("SELECT * FROM kpis ORDER BY period, id")
    series = {}
    for k in kpis:
        series.setdefault(k["name"], []).append(k)
    pipeline = db.query("SELECT stage, COUNT(*) AS n, AVG(fit_score) AS fit FROM prospects GROUP BY stage")
    return render_template("growth.html", kpis=analytics.practice_kpis(), series=series, pipeline=pipeline,
                           goals=db.query("SELECT * FROM goals ORDER BY status, due"),
                           groups=grouped(["growth_plan", "vestige_ip", "radar", "health_check", "course_correction"], scope="growth"),
                           today=date.today())


# ---------------------------------------------------------- deliverables ----

@bp.route("/deliverables")
def deliverables():
    rows = db.query("SELECT decks.*, brands.name AS brand_name FROM decks LEFT JOIN brands ON brands.id = decks.brand_id "
                    "ORDER BY decks.updated_at DESC")
    return render_template("deliverables.html", decks=rows)


@bp.route("/deliverables/new", methods=["GET", "POST"])
def deck_new():
    brands = db.query("SELECT id, name FROM brands ORDER BY name")
    source = request.values.get("source", "")
    brand_id = _int(source[2:]) if source.startswith("b:") else None
    scope = source[2:] if source.startswith("s:") else None
    brand = get_brand(brand_id) if brand_id else None
    if request.method == "POST" and request.form.get("compose"):
        ids = [_int(i) for i in request.form.getlist("item")]
        items = decks.items_for_deck(ids=ids) if ids else []
        if not items:
            flash("Select at least one piece of work.", "error")
            return redirect(url_for("v.deck_new", source=source))
        title = request.form.get("title") or (f"{brand['name']} — Relationship Strategy" if brand else "Vestige — Growth Strategy")
        audience = request.form.get("audience", "client")
        model = "assembled"
        if request.form.get("compose") == "ai":
            try:
                slides, model = decks.compose_with_ai(title, brand, items, audience, request.form.get("provider"))
            except ai.AIError as e:
                flash(str(e), "error")
                return redirect(url_for("v.deck_new", source=source))
        else:
            slides = decks.assemble(title, brand, items, audience)
        deck_id = db.insert("decks", {"brand_id": brand_id, "title": title, "subtitle": "", "audience": audience,
                                      "slides": slides, "model": model, "created_at": db.now(), "updated_at": db.now()})
        return redirect(url_for("v.deck_edit", deck_id=deck_id))
    items = decks.items_for_deck(brand_id=brand_id, scope=scope) if (brand_id or scope) else []
    return render_template("deck_new.html", brands=brands, source=source, brand=brand, items=items)


def get_deck(deck_id):
    return db.query("SELECT * FROM decks WHERE id = ?", (deck_id,), one=True) or abort(404)


@bp.route("/deliverables/<int:deck_id>", methods=["GET", "POST"])
def deck_edit(deck_id):
    deck = get_deck(deck_id)
    if request.method == "POST":
        try:
            slides = json.loads(request.form.get("slides", "[]"))
            assert isinstance(slides, list)
        except (ValueError, AssertionError):
            flash("Could not save slides.", "error")
            return redirect(request.path)
        db.update("decks", deck_id, {"slides": slides, "title": request.form.get("title", deck["title"]),
                                     "updated_at": db.now()})
        flash("Deck saved.", "ok")
        return redirect(request.path)
    brand = get_brand(deck["brand_id"]) if deck["brand_id"] else None
    return render_template("deck_edit.html", deck=deck, brand=brand, types=decks.SLIDE_TYPES)


@bp.route("/deliverables/<int:deck_id>/view")
def deck_view(deck_id):
    deck = get_deck(deck_id)
    brand = get_brand(deck["brand_id"]) if deck["brand_id"] else None
    return render_template("deck_view.html", deck=deck, brand=brand)


@bp.route("/deliverables/<int:deck_id>/pptx")
def deck_pptx(deck_id):
    deck = get_deck(deck_id)
    brand = get_brand(deck["brand_id"]) if deck["brand_id"] else None
    buf = decks.to_pptx(deck, brand["accent_color"] if brand else "#8C6A4A")
    name = re.sub(r"[^A-Za-z0-9]+", "-", deck["title"]).strip("-") or "vestige-deck"
    return send_file(buf, as_attachment=True, download_name=f"{name}.pptx",
                     mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation")


@bp.post("/deliverables/<int:deck_id>/delete")
def deck_delete(deck_id):
    get_deck(deck_id)
    db.delete("decks", deck_id)
    return redirect(url_for("v.deliverables"))


# ------------------------------------------------------------ diagnostics ----

def get_diag(brand_id, diag_id):
    return db.query("SELECT * FROM diagnostics WHERE id = ? AND brand_id = ?", (diag_id, brand_id), one=True) or abort(404)


def readiness(brand, stats):
    comps = db.query("SELECT actions FROM competitors WHERE brand_id = ?", (brand["id"],))
    clients = stats["clients"]
    n = len(clients) or 1
    return [
        ("Client base", len(clients) >= 6, f"{len(clients)} clients" + ("" if len(clients) >= 30 else " — 30+ gives sturdier archetypes")),
        ("Interests", any(c["interests"] for c in clients), f"{round(100 * sum(bool(c['interests']) for c in clients) / n)}% of clients"),
        ("Purchase history", any(c.get("purchase_count") for c in clients), f"{round(100 * sum(bool(c.get('purchase_count')) for c in clients) / n)}% of clients"),
        ("Cross-industry purchases", any(c["cross_purchases"] for c in clients), f"{round(100 * sum(bool(c['cross_purchases']) for c in clients) / n)}% of clients"),
        ("Brand identity", bool(brand["heritage"] and brand["tone_of_voice"]), "heritage, values, codes, tone"),
        ("Current engagement & retention strategy", bool(brand["current_strategy"]), "what they do today"),
        ("Resource allocation", bool(brand["resource_allocation"]), "where the budget goes"),
        ("Competitor actions", any(c["actions"] for c in comps), f"{sum(bool(c['actions']) for c in comps)} of {len(comps)} competitors"),
    ]


@bp.route("/b/<int:brand_id>/diagnostics", methods=["GET", "POST"])
def diagnostics(brand_id):
    b = get_brand(brand_id)
    if request.method == "POST":
        if db.scalar("SELECT COUNT(*) FROM clients WHERE brand_id = ?", (brand_id,)) < 6:
            flash("Import at least 6 clients before running a diagnostic.", "error")
            return redirect(request.path)
        diag_id = diagnostic.start(brand_id, request.form.get("brief", ""), request.form.get("provider") or None)
        return redirect(url_for("v.diagnostic_view", brand_id=brand_id, diag_id=diag_id))
    stats = analytics.portfolio_stats(brand_id)
    runs = db.query("SELECT id, status, stage, error, model, created_at, finished_at, deck_id FROM diagnostics "
                    "WHERE brand_id = ? ORDER BY id DESC", (brand_id,))
    return render_template("diagnostics.html", brand=b, runs=runs, ready=readiness(b, stats), stats=stats)


@bp.route("/b/<int:brand_id>/diagnostics/<int:diag_id>")
def diagnostic_view(brand_id, diag_id):
    b = get_brand(brand_id)
    d = get_diag(brand_id, diag_id)
    return render_template("diagnostic.html", brand=b, d=d, stages=diagnostic.STAGES, standalone=False)


@bp.route("/b/<int:brand_id>/diagnostics/<int:diag_id>/report")
def diagnostic_report(brand_id, diag_id):
    b = get_brand(brand_id)
    d = get_diag(brand_id, diag_id)
    return render_template("report.html", brand=b, d=d, standalone=True)


@bp.route("/b/<int:brand_id>/diagnostics/<int:diag_id>/status")
def diagnostic_status(brand_id, diag_id):
    d = get_diag(brand_id, diag_id)
    return jsonify(status=d["status"], stage=d["stage"], error=d["error"])


@bp.post("/b/<int:brand_id>/diagnostics/<int:diag_id>/deck")
def diagnostic_deck(brand_id, diag_id):
    b = get_brand(brand_id)
    d = get_diag(brand_id, diag_id)
    if d["status"] != "done":
        abort(400)
    slides = decks.from_diagnostic(b, d)
    deck_id = db.insert("decks", {"brand_id": brand_id, "title": f"{b['name']} — Engagement Diagnostic",
                                  "subtitle": "", "audience": "client", "slides": slides, "model": d["model"],
                                  "created_at": db.now(), "updated_at": db.now()})
    db.update("diagnostics", diag_id, {"deck_id": deck_id})
    return redirect(url_for("v.deck_edit", deck_id=deck_id))


@bp.post("/b/<int:brand_id>/diagnostics/<int:diag_id>/delete")
def diagnostic_delete(brand_id, diag_id):
    get_diag(brand_id, diag_id)
    db.delete("diagnostics", diag_id)
    return redirect(url_for("v.diagnostics", brand_id=brand_id))


# ------------------------------------------------------------- prospects ----

def get_prospect(pid):
    return db.query("SELECT * FROM prospects WHERE id = ?", (pid,), one=True) or abort(404)


@bp.route("/prospects", methods=["GET", "POST"])
def prospects():
    if request.method == "POST":
        f = request.form
        if f.get("action") == "radar":
            if not f.get("thesis", "").strip():
                flash("Describe what you are looking for.", "error")
                return redirect(request.path)
            try:
                n, model, web = prospecting.radar(f["thesis"], _int(f.get("n"), 8, 3, 15), f.get("provider") or None)
                flash(f"{n} candidate companies added as 'Suggested' ({model}{'' if web else ', no web access'}).", "ok")
            except ai.AIError as e:
                flash(str(e), "error")
            return redirect(request.path)
        if not f.get("company", "").strip():
            flash("Company name is required.", "error")
            return redirect(request.path)
        pid = db.insert("prospects", {k: f.get(k, "").strip() for k in ("company", "sector", "market", "website", "why",
                                                                          "material")} |
                        {"stage": "Identified", "created_at": db.now(), "updated_at": db.now()})
        if f.get("research"):
            prospecting.start(pid, f.get("provider") or None)
        return redirect(url_for("v.prospect", pid=pid))
    rows = db.query("SELECT * FROM prospects ORDER BY COALESCE(fit_score, -1) DESC, updated_at DESC")
    board = {s: [p for p in rows if p["stage"] == s] for s in prospecting.STAGES}
    return render_template("prospects.html", board=board, stages=prospecting.STAGES, total=len(rows))


@bp.route("/prospects/<int:pid>", methods=["GET", "POST"])
def prospect(pid):
    p = get_prospect(pid)
    if request.method == "POST":
        f = request.form
        act = f.get("action")
        if act == "research":
            if f.get("material") is not None:
                db.update("prospects", pid, {"material": f.get("material", "")})
            prospecting.start(pid, f.get("provider") or None)
        elif act == "update":
            db.update("prospects", pid, {k: f.get(k, p[k]) for k in ("company", "sector", "market", "website", "stage",
                                                                   "notes")} | {"updated_at": db.now()})
        elif act == "deck":
            slides = decks.from_prospect(p)
            deck_id = db.insert("decks", {"title": f"{p['company']} × Vestige", "subtitle": "", "audience": "prospect",
                                          "slides": slides, "model": p["model"], "created_at": db.now(),
                                          "updated_at": db.now()})
            db.update("prospects", pid, {"deck_id": deck_id})
            return redirect(url_for("v.deck_edit", deck_id=deck_id))
        elif act == "convert":
            brand_id = prospecting.to_brand(p)
            flash(f"{p['company']} is now a client engagement. Import their CRM to run the diagnostic.", "ok")
            return redirect(url_for("v.diagnostics", brand_id=brand_id))
        elif act == "delete":
            db.delete("prospects", pid)
            return redirect(url_for("v.prospects"))
        return redirect(url_for("v.prospect", pid=pid))
    return render_template("prospect.html", p=p, stages=prospecting.STAGES, run_stages=prospecting.RUN_STAGES)


@bp.route("/prospects/<int:pid>/report")
def prospect_report(pid):
    return render_template("prospect_report.html", p=get_prospect(pid))
