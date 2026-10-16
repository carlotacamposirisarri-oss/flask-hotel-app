"""Deliverable Studio: assemble decks from work items, AI-compose them, export PPTX."""
import io
from datetime import date

from . import ai, analytics, db
from .prompts import DECK_PROMPT, KINDS, VESTIGE_SYSTEM

SLIDE_TYPES = ["cover", "section", "text", "metrics", "bars", "matrix", "quote", "closing"]


def _bullets_from_payload(kind, payload, limit=6):
    out = []
    for key, val in payload.items():
        if key in ("month",):
            continue
        label = key.replace("_", " ").capitalize()
        if isinstance(val, list):
            for v in val[:3]:
                if isinstance(v, dict):
                    v = " · ".join(str(x) for x in v.values())
                out.append(f"{label}: {v}")
        elif isinstance(val, dict):
            out.append(f"{label}: " + "; ".join(f"{k} {v}" for k, v in val.items()))
        elif val not in (None, ""):
            out.append(f"{label}: {val}")
    return out[:limit]


def data_slides(brand):
    if not brand:
        x = analytics.cross_brand()
        return [{"type": "bars", "title": "Interest clusters across the Vestige portfolio",
                 "bars": [{"label": k, "value": v} for k, v in x["interests"][:8]]}]
    s = analytics.portfolio_stats(brand["id"])
    return [
        {"type": "metrics", "title": "The portfolio at a glance", "metrics": [
            {"label": "Clients tracked", "value": str(s["count"])},
            {"label": "Average engagement", "value": str(s["avg_engagement"])},
            {"label": "Loyal & ambassadors", "value": str(s["loyal"])},
            {"label": "At risk or dormant", "value": str(s["at_risk"])},
        ]},
        {"type": "bars", "title": "What moves these clients — interest clusters",
         "bars": [{"label": k, "value": v} for k, v in s["interests"][:8]]},
    ]


def assemble(title, brand, items, audience):
    """Deterministic deck: no AI needed, Vestige refines afterwards."""
    subtitle = f"Prepared by Vestige for {brand['name']}" if brand else "Vestige · Internal strategy"
    slides = [{"type": "cover", "title": title, "subtitle": f"{subtitle} · {date.today():%B %Y}"}]
    slides.append({"type": "text", "title": "Executive summary",
                   "body": "The priorities that emerged from our work, in order of impact.",
                   "bullets": [i["title"] for i in sorted(items, key=lambda i: -(i["impact"] * i["urgency"]))[:6]]})
    slides += data_slides(brand)
    by_kind = {}
    for it in items:
        by_kind.setdefault(it["kind"], []).append(it)
    for kind, its in by_kind.items():
        slides.append({"type": "section", "title": KINDS.get(kind, {}).get("plural", kind.title()),
                       "subtitle": f"{len(its)} recommendation{'s' if len(its) != 1 else ''}"})
        for it in its:
            body = it["summary"] + (f"\n\nVestige note: {it['annotation']}" if it["annotation"] else "")
            slides.append({"type": "text", "title": it["title"], "body": body,
                           "bullets": _bullets_from_payload(kind, it["payload"])})
    slides.append({"type": "closing", "title": "Next steps", "bullets": [
        "Validate priorities together", "Assign owners and timing", "Activate the first initiative",
        "Review signals and impact in 90 days"]})
    return slides


def from_diagnostic(brand, d):
    """Deck from a completed Engagement Diagnostic — numbers come from the data, words from the analysis."""
    seg, arch, cx, st = d["segmentation"], d["archetypes"], d["crossexam"], d["strategy"]
    by_id = {s["id"]: s for s in seg.get("segments", [])}
    archs = arch.get("archetypes", [])
    name = lambda a: a.get("name") or f"Segment {a.get('segment_id')}"  # noqa: E731
    q = seg.get("quality", {})
    top = max(seg.get("segments", []), key=lambda s: s["value_pct"], default={})
    risk_value = sum(s["value"] * s["at_risk_pct"] / 100 for s in seg.get("segments", []))
    total_value = sum(s["value"] for s in seg.get("segments", [])) or 1
    slides = [
        {"type": "cover", "title": f"{brand['name']} — Engagement Diagnostic",
         "subtitle": f"Prepared by Vestige · {date.today():%B %Y}"},
        {"type": "quote", "title": "The thesis", "body": st.get("headline", "")},
        {"type": "text", "title": "Executive summary", "bullets": st.get("executive_summary", [])},
        {"type": "metrics", "title": "The client base, read through behaviour", "metrics": [
            {"label": "Clients analysed", "value": str(q.get("clients", ""))},
            {"label": "Behavioural archetypes", "value": str(q.get("k", ""))},
            {"label": f"Value held by {name(next((a for a in archs if a.get('segment_id') == top.get('id')), {'segment_id': top.get('id')}))}",
             "value": f"{top.get('value_pct', 0)}%"},
            {"label": "Value in at-risk relationships", "value": f"{round(100 * risk_value / total_value)}%"},
        ]},
        {"type": "section", "title": "Who your clients really are", "subtitle": arch.get("segmentation_reading", "")},
        {"type": "bars", "title": "Share of client value by archetype",
         "bars": [{"label": name(a), "value": by_id.get(a.get("segment_id"), {}).get("value_pct", 0)} for a in archs]},
    ]
    for a in archs:
        s = by_id.get(a.get("segment_id"), {})
        slides.append({"type": "text", "title": name(a),
                       "body": f"{a.get('essence', '')}\n\n{s.get('size_pct', '?')}% of clients · {s.get('value_pct', '?')}% of value · "
                               f"{s.get('at_risk_pct', '?')}% at risk\n\n{a.get('relationship_to_brand', '')}",
                       "bullets": (a.get("defining_behaviours") or [])[:4] + (a.get("emotional_drivers") or [])[:2]})
    matrix = cx.get("matrix", [])
    slides += [
        {"type": "section", "title": "The diagnosis", "subtitle": cx.get("synthesis", "")},
        {"type": "matrix", "title": "Identity, current strategy and competitive pressure",
         "columns": ["Identity fit", "Strategy coverage", "Competitor pressure"],
         "rows": [{"label": m.get("archetype", ""), "values": [m.get("identity_fit", 0), m.get("strategy_coverage", 0),
                                                              m.get("competitor_pressure", 0)]} for m in matrix]},
        {"type": "text", "title": "Where effort is misdirected",
         "bullets": [f"{w.get('title')} — {w.get('evidence', '')}" for w in cx.get("weaknesses", [])][:6]},
        {"type": "text", "title": "Where the maison can win",
         "bullets": [f"{o.get('title')} — {o.get('value_at_stake', '')}" for o in cx.get("opportunities", [])][:6]},
        {"type": "section", "title": "The strategy", "subtitle": (st.get("north_star") or {}).get("concept", "")},
        {"type": "text", "title": "North star", "body": f"{(st.get('north_star') or {}).get('concept', '')}\n\n"
                                                        f"{(st.get('north_star') or {}).get('why_it_is_ownable', '')}"},
        {"type": "bars", "title": "Redirecting resources (share of budget moved)",
         "bars": [{"label": f"{r.get('from')} → {r.get('to')}", "value": r.get("shift_pct", 0)} for r in st.get("reallocation", [])]},
        {"type": "bars", "title": "Target allocation (%)",
         "bars": [{"label": t.get("line", ""), "value": t.get("pct", 0)} for t in st.get("target_allocation", [])]},
    ]
    for p in st.get("archetype_plays", []):
        slides.append({"type": "text", "title": f"{p.get('archetype')}: {p.get('experiential_pillar', '')}",
                       "body": f"{p.get('objective', '')}\n\nCadence: {p.get('cadence', '')}",
                       "bullets": [f"{e.get('name')} — {e.get('format')} · emotional impact {e.get('emotional_impact')}/5 · "
                                   f"{e.get('commercial_kpi')}: {e.get('expected_result')}"
                                   for e in p.get("signature_experiences", [])]})
    slides += [
        {"type": "text", "title": "Twelve-month roadmap",
         "bullets": [f"{r.get('quarter')}: {'; '.join(r.get('initiatives', []))}" for r in st.get("roadmap", [])]},
        {"type": "text", "title": "Measuring emotion and commerce",
         "body": "Emotional: " + "; ".join((st.get("kpis") or {}).get("emotional", [])),
         "bullets": ["Commercial: " + k for k in (st.get("kpis") or {}).get("commercial", [])]},
        {"type": "closing", "title": "The first 90 days", "bullets": st.get("quick_wins", [])},
    ]
    return slides


def from_prospect(p):
    """Pitch deck built on the prospect's own public evidence."""
    d, pt = p["dossier"] or {}, p["pitch"] or {}
    pitch = pt.get("pitch", {})
    signals = d.get("problem_signals", [])
    slides = [
        {"type": "cover", "title": f"{p['company']} × Vestige", "subtitle": f"A point of view · {date.today():%B %Y}"},
        {"type": "quote", "title": "", "body": pitch.get("hook", "")},
        {"type": "text", "title": "What we observe", "body": pt.get("the_problem", ""),
         "bullets": [s.get("signal", "") for s in signals[:5]]},
        {"type": "text", "title": "The market around you",
         "bullets": [f"{c.get('name')}: {c.get('recent_actions', '')}" for c in d.get("competitors", [])[:5]]},
        {"type": "text", "title": "Who your clients are becoming",
         "bullets": [f"{a.get('name')} — {a.get('rationale', '')}" for a in d.get("likely_archetypes", [])[:5]]},
        {"type": "section", "title": "Where we see the opportunity", "subtitle": pitch.get("angle", "")},
    ]
    for h in pt.get("opportunity_hypotheses", [])[:4]:
        slides.append({"type": "text", "title": h.get("hypothesis", ""), "body": h.get("evidence", ""),
                       "bullets": [f"Vestige: {h.get('vestige_answer', '')}", f"Value: {h.get('value', '')}"]})
    slides += [
        {"type": "text", "title": "Why Vestige", "bullets": pitch.get("proof_points", [])},
        {"type": "text", "title": "A first step", "body": pitch.get("entry_offer", "")},
        {"type": "closing", "title": "Next steps", "bullets": pt.get("next_steps", [])},
    ]
    return slides


def compose_with_ai(title, brand, items, audience, provider=None):
    context = analytics.brand_codes(brand) if brand else "## Audience: Vestige internal leadership"
    work = "\n\n".join(
        f"[{KINDS.get(i['kind'], {}).get('label', i['kind'])}] {i['title']}\n{i['summary']}\n"
        f"Details: {i['payload']}\nVestige annotation: {i['annotation']}" for i in items)
    data, model = ai.complete_json(VESTIGE_SYSTEM, DECK_PROMPT.format(
        context=context, title=title, audience=audience, work=work), provider)
    slides = [s for s in data.get("slides", []) if isinstance(s, dict) and s.get("type") in SLIDE_TYPES]
    if not slides:
        raise ai.AIError("The model returned no usable slides.")
    # Data slides are computed, not generated: insert real numbers after the summary.
    slides[2:2] = data_slides(brand)
    return slides, model


# ------------------------------------------------------------------ PPTX ----

def _rgb(hex_color):
    from pptx.dml.color import RGBColor

    h = hex_color.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def to_pptx(deck, accent="#8C6A4A"):
    from pptx import Presentation
    from pptx.chart.data import CategoryChartData
    from pptx.enum.chart import XL_CHART_TYPE
    from pptx.util import Inches, Pt

    bone, charcoal, sand = _rgb("#F6F2EA"), _rgb("#2B2724"), _rgb("#E6DCCB")
    acc = _rgb(accent or "#8C6A4A")
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    blank = prs.slide_layouts[6]

    def bg(slide, color):
        fill = slide.background.fill
        fill.solid()
        fill.fore_color.rgb = color

    def text(slide, x, y, w, h, content, size, color, serif=False, bold=False):
        tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = True
        lines = content if isinstance(content, list) else [content]
        for i, line in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = str(line)
            p.font.size = Pt(size)
            p.font.color.rgb = color
            p.font.bold = bold
            p.font.name = "Georgia" if serif else "Helvetica"
            p.space_after = Pt(size * 0.6)
        return tb

    for s in deck["slides"]:
        slide = prs.slides.add_slide(blank)
        t = s.get("type")
        if t in ("cover", "closing", "section"):
            bg(slide, charcoal if t != "section" else acc)
            text(slide, 0.9, 0.6, 6, 0.4, "VESTIGE", 11, sand, bold=True)
            text(slide, 0.9, 2.4, 11.5, 1.8, s.get("title", ""), 44 if t == "cover" else 36, bone, serif=True)
            if s.get("subtitle"):
                text(slide, 0.9, 4.3, 11.5, 0.8, s["subtitle"], 16, sand)
            if s.get("bullets"):
                text(slide, 0.9, 4.0, 11.5, 3, [f"—  {b}" for b in s["bullets"]], 16, sand)
            continue
        bg(slide, bone)
        text(slide, 0.9, 0.5, 6, 0.3, "VESTIGE", 9, acc, bold=True)
        text(slide, 0.9, 0.9, 11.5, 1.2, s.get("title", ""), 30, charcoal, serif=True)
        if t == "metrics":
            ms = s.get("metrics", [])[:4]
            for i, m in enumerate(ms):
                x = 0.9 + i * (11.5 / max(len(ms), 1))
                text(slide, x, 2.8, 2.8, 1.2, m.get("value", ""), 40, acc, serif=True)
                text(slide, x, 4.0, 2.8, 0.8, m.get("label", ""), 13, charcoal)
        elif t == "bars" and s.get("bars"):
            cd = CategoryChartData()
            cd.categories = [b["label"] for b in s["bars"]]
            cd.add_series("Clients", [b["value"] for b in s["bars"]])
            chart = slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.9), Inches(2.1),
                                           Inches(11.5), Inches(4.9), cd).chart
            chart.has_legend = False
            plot = chart.plots[0]
            plot.gap_width = 60
            plot.series[0].format.fill.solid()
            plot.series[0].format.fill.fore_color.rgb = acc
            chart.category_axis.reverse_order = True
            chart.category_axis.tick_labels.font.size = Pt(12)
            chart.value_axis.visible = False
            chart.value_axis.has_major_gridlines = False
        elif t == "matrix" and s.get("rows"):
            cols = s.get("columns", [])
            rows = s["rows"]
            tbl = slide.shapes.add_table(len(rows) + 1, len(cols) + 1, Inches(0.9), Inches(2.1), Inches(11.5),
                                         Inches(0.6 * (len(rows) + 1))).table
            for j, c in enumerate([""] + cols):
                cell = tbl.cell(0, j)
                cell.text = str(c)
                cell.fill.solid()
                cell.fill.fore_color.rgb = charcoal
                cell.text_frame.paragraphs[0].font.color.rgb = bone
                cell.text_frame.paragraphs[0].font.size = Pt(12)
            for i, r in enumerate(rows, start=1):
                tbl.cell(i, 0).text = str(r.get("label", ""))
                tbl.cell(i, 0).text_frame.paragraphs[0].font.size = Pt(12)
                for j, v in enumerate(r.get("values", []), start=1):
                    cell = tbl.cell(i, j)
                    cell.text = str(v)
                    cell.fill.solid()
                    try:
                        level = max(0, min(100, float(v))) / 100
                    except (TypeError, ValueError):
                        level = 0
                    base = (0xF6, 0xF2, 0xEA)
                    tgt = tuple(int((accent or "#8C6A4A").lstrip("#")[k:k + 2], 16) for k in (0, 2, 4))
                    from pptx.dml.color import RGBColor
                    cell.fill.fore_color.rgb = RGBColor(*[int(b + (t - b) * level) for b, t in zip(base, tgt)])
                    para = cell.text_frame.paragraphs[0]
                    para.font.size = Pt(13)
                    para.font.color.rgb = bone if level > .55 else charcoal
        elif t == "quote":
            text(slide, 1.5, 2.5, 10.3, 3.5, f"“{s.get('body', '')}”", 28, charcoal, serif=True)
        else:
            if s.get("body"):
                text(slide, 0.9, 2.1, 5.6 if s.get("bullets") else 11.5, 4.8, s["body"].split("\n\n"), 15, charcoal)
            if s.get("bullets"):
                text(slide, 7.0 if s.get("body") else 0.9, 2.1, 5.4 if s.get("body") else 11.5, 4.8,
                     [f"—  {b}" for b in s["bullets"]], 13, charcoal)
    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf


def items_for_deck(brand_id=None, scope=None, ids=None):
    if ids:
        marks = ",".join("?" for _ in ids)
        return db.query(f"SELECT * FROM items WHERE id IN ({marks}) ORDER BY kind, priority DESC, id", ids)
    if brand_id:
        return db.query("SELECT * FROM items WHERE brand_id = ? AND status != 'dismissed' ORDER BY kind, id",
                        (brand_id,))
    return db.query("SELECT * FROM items WHERE scope = ? AND status != 'dismissed' ORDER BY kind, id", (scope,))
