"""Load a fictional demo portfolio so every screen has something to show.

    python -m vestige.seed          # adds demo data (skips if brands exist)
    python -m vestige.seed --reset  # wipes the database first

All maisons, clients and competitors below are invented. Demo work items are
stamped "demo-seed" so they are never mistaken for real AI output.
"""
import os
import random
import sys
from datetime import date, timedelta

from . import create_app, db

BRANDS = [
    {
        "name": "Maison Aurèle", "sector": "Haute joaillerie", "market": "Europe, GCC, Greater China",
        "heritage": "Founded in 1891 on Place Vendôme by Céleste Aurèle, a lapidary who cut stones for the Ballets Russes. "
                    "Known for the 'lumière captive' setting and archive of 40,000 gouache drawings.",
        "core_values": "Savoir-faire, poetry, discretion, transmission between generations",
        "visual_codes": "Ivory and lapis blue; the Aurèle knot; gouache sketches; the Vendôme salon's oval mirror",
        "tone_of_voice": "Poetic, intimate, cultivated. Speaks in stories, never in prices. Avoids superlatives.",
        "archetypes": "The Collector: builds a coherent collection over decades\nThe Heir: inherited pieces, seeks own voice\n"
                      "The Cultural Patron: arts boards, biennales, foundations\nThe Next-Gen Tastemaker: under 35, digital-native, values meaning",
        "positioning": "The poetic counterpoint to logo-driven jewellery: high-jewellery as heirloom and cultural artefact.",
        "strategic_gaps": "Relationships depend on 4 senior advisors; Next-gen clients buy once and disappear; events feel interchangeable with competitors.",
        "accent_color": "#3E5A7A", "map_x": 30, "map_y": 82,
    },
    {
        "name": "Vauclain Genève", "sector": "Haute horlogerie", "market": "Europe, USA, Japan, Singapore",
        "heritage": "Independent manufacture since 1847 in the Vallée de Joux; seven generations of the Vauclain family; "
                    "hand-finished minute repeaters and the 1903 astronomical pocket watch.",
        "core_values": "Patience, mechanical truth, independence, family",
        "visual_codes": "Forest green and brushed steel; guilloché; the Joux pine; workshop light",
        "tone_of_voice": "Precise, understated, quietly confident. Engineer's humility.",
        "archetypes": "The Connoisseur: knows calibres, wants access to watchmakers\nThe Self-Made Visionary: founder, time-poor, values rarity\n"
                      "The Discreet Traditionalist: family office, old money, avoids exposure\nThe Global Nomad: lives across three cities",
        "positioning": "The connoisseur's independent: rarer than the big groups, more human than boutique brands.",
        "strategic_gaps": "Allocation feels transactional; no community between owners; US clients under-served vs Europe.",
        "accent_color": "#3F5B45", "map_x": 22, "map_y": 70,
    },
]

COMPETITORS = {
    "Maison Aurèle": [
        ("Orsini Gioielli", "Roman exuberance, colour and celebrity", "VIC, top 200", "Cannes, Met Gala, big launches", 70, 60),
        ("Lumière de Seine", "Parisian high-jewellery of a luxury group", "VVIC, top 500", "Biennale presence, art foundation", 55, 85),
        ("Atelier Kōyō", "Japanese minimalism, nature motifs", "Collectors, Asia", "Kyoto salon, ceramic collaborations", 75, 72),
    ],
    "Vauclain Genève": [
        ("Hartmann & Söhne", "German precision, sporting complications", "Connoisseurs, top 300", "Motorsport partner, collectors club", 60, 55),
        ("Maison Delorme", "Group-owned grande complication house", "VVIC", "Auction records, private salons", 40, 88),
        ("Kessler Independent", "Young avant-garde independent", "Next-gen collectors", "Instagram, design fairs", 88, 62),
    ],
}

FIRST = ["Isabelle", "Hiroshi", "Leila", "Alessandro", "Margaux", "Omar", "Chen", "Sofia", "Frederik", "Amara", "Julian",
         "Noor", "Elena", "Takumi", "Charlotte", "Rafael", "Mei", "Victoria", "Karim", "Astrid", "Lorenzo", "Yasmin", "Henri", "Ingrid"]
LAST = ["Delacroix-Brun", "Tanaka", "Al-Mansouri", "Ferrante", "de Villeneuve", "Haddad", "Liang", "Marchetti", "Lindqvist",
        "Okafor", "Whitmore", "Al-Thani", "Rossi", "Mori", "Ashford", "Castellanos", "Wong", "Harrington", "Benali", "Sørensen",
        "Visconti", "Farouk", "de la Roche", "Berg"]
PLACES = [("France", "Paris"), ("Japan", "Tokyo"), ("UAE", "Dubai"), ("Italy", "Milan"), ("Switzerland", "Geneva"),
          ("Saudi Arabia", "Riyadh"), ("China", "Shanghai"), ("UK", "London"), ("USA", "New York"), ("Singapore", "Singapore"),
          ("Qatar", "Doha"), ("Monaco", "Monaco"), ("USA", "Los Angeles"), ("Hong Kong", "Hong Kong")]
CIRCLES = ["Fondation Beyeler patrons", "Yacht Club de Monaco", "Art Basel collectors circle", "Polo Club Saint-Tropez",
           "Serpentine Council", "Opéra de Paris AROP", "Geneva Watch Club", "YPO", "Glyndebourne members", "Louvre Abu Dhabi friends"]
PURCHASES = ["Riva Aquariva", "Patek Philippe Nautilus", "Hermès Kelly collection", "Château Margaux en primeur",
             "Ferrari SF90", "Aman residences", "Contemporary African art", "Hasselblad archive prints", "Bugatti Chiron",
             "Loro Piana bespoke", "Racehorse share", "Private island villa"]
SIGNALS = ["Attended 3 salons this year, bought twice", "No visit in 14 months after a strong 2024",
           "Engages with archive stories, ignores product launches", "Asked about apprenticeships for daughter",
           "Bought gift pieces only — never for self", "Responds within minutes to advisor, prefers WhatsApp",
           "Cancelled last two invitations", "Referred two friends in 2025", "Interested in bespoke commissions",
           "Follows competitor's Biennale programme closely"]
CLUSTERS = ["Arts", "Travel", "Gastronomy", "Philanthropy", "Motorsport", "Real Estate", "Collectibles", "Wine & Spirits",
            "Wellness", "Sailing", "Equestrian", "Music", "Design & Architecture", "Family"]
PHASES = ["Discovery", "Courtship", "Engaged", "Engaged", "Loyal", "Loyal", "Ambassador", "At risk", "Dormant"]

ITEMS = {
    "Maison Aurèle": [
        ("insight", "Next-gen buyers vanish after the first piece", "Six of eight Next-Gen Tastemakers bought once in 2025 and have not "
         "returned; none were invited to anything afterwards.", 5, 5, None, {"category": "risk",
         "evidence": "Phase 'Dormant' or 'At risk' for 6/8 clients under 35; no events logged after purchase",
         "recommended_action": "Design a 90-day post-purchase 'apprenticeship' journey — owner: CRM lead, start next month",
         "clients_concerned": "The Next-Gen Tastemaker"}),
        ("insight", "Arts patrons over-index — and Lumière de Seine knows it", "Cultural Patrons are the most valuable segment and "
         "the one most exposed to the competitor's Biennale programme.", 4, 5, None, {"category": "opportunity",
         "evidence": "Arts is the #1 interest cluster; 3 patrons follow the competitor's foundation",
         "recommended_action": "Claim a distinct cultural territory: the Aurèle gouache archive as living art",
         "clients_concerned": "The Cultural Patron"}),
        ("initiative", "The Gouache Night at Vendôme", "An after-hours salon where 12 collectors watch the archive's gouaches come to life "
         "beside the stones they inspired.", 3, 5, 3, {"format": "Private salon", "interest_clusters": ["Arts", "Collectibles"],
         "target_archetypes": "The Collector, The Cultural Patron", "emotional_impact": 5, "engagement_lift": "+20% bespoke enquiries",
         "guest_count": "12", "budget_band": "€€", "rationale": "Makes heritage tangible; impossible for rivals to copy"}),
        ("initiative", "Venice, through the lapidary's eye", "A Biennale journey led by the head lapidary, ending in a palazzo dinner.",
         3, 4, 5, {"format": "Cultural journey", "interest_clusters": ["Arts", "Travel", "Gastronomy"], "emotional_impact": 4,
                   "engagement_lift": "+3 ambassadors", "guest_count": "16", "budget_band": "€€€"}),
        ("collaboration", "A residency with a ceramics atelier", "Co-create a capsule of jewelled ceramics with a contemporary "
         "ceramicist.", 2, 4, None, {"partner": "Contemporary ceramics atelier", "category": "Craft & design", "compatibility": 82,
         "rationale": "Shared vocabulary of hand, material and time", "brand_fit_check": "Avoid Japanese houses already tied to Atelier Kōyō",
         "risk_level": "medium", "rival_conflict": "Atelier Kōyō runs ceramic collaborations"}),
        ("audit", "Events are interchangeable", "Current events (champagne, launch, photo wall) could belong to any maison.", 4, 4, None,
         {"category": "generic approach", "severity": "high", "rationale": "No heritage element in 5 of the last 6 events",
          "pivot": "Every event starts from an archive object and a craftsperson", "expected_impact": "Higher recall and referral",
          "next_steps": ["Audit the 2026 calendar", "Brief the archive team", "Retire the launch-party format"]}),
    ],
    "Vauclain Genève": [
        ("insight", "Allocation feels like a waitlist, not a relationship", "Connoisseurs describe allocation as opaque; two strong "
         "clients moved to Hartmann & Söhne.", 5, 4, None, {"category": "risk",
         "evidence": "2 Connoisseurs 'At risk' with competitor purchases logged",
         "recommended_action": "Introduce a transparent 'workbench letter' from the watchmaker during the wait",
         "clients_concerned": "The Connoisseur"}),
        ("initiative", "A winter week in the Vallée de Joux", "Owners spend two days at the bench beside the watchmaker finishing "
         "a component of their own watch.", 3, 5, 1, {"format": "Manufacture immersion", "interest_clusters": ["Collectibles", "Design & Architecture"],
         "emotional_impact": 5, "engagement_lift": "+30% referral rate", "guest_count": "6", "budget_band": "€€"}),
        ("initiative", "The Owners' Table in New York", "A quiet dinner series for US owners hosted by a Vauclain family member.",
         3, 4, 10, {"format": "Private dinner", "interest_clusters": ["Gastronomy", "Wine & Spirits"], "emotional_impact": 4,
                    "engagement_lift": "Close US service gap", "guest_count": "10", "budget_band": "€€"}),
        ("competitive", "Hartmann & Söhne owns the sporting connoisseur", "Strong motorsport presence wins the Self-Made Visionaries "
         "who also race.", 4, 4, None, {"competitor": "Hartmann & Söhne", "shared_tiers": "Connoisseurs, top 300",
         "affinity_overlap": "Motorsport, Collectibles", "engagement_gaps": "They run an owners' club; Vauclain has none",
         "whitespace": ["Mechanical art over speed", "Family-to-family access"], "threats": ["Motorsport-led connoisseurs"],
         "threat_level": "high"}),
    ],
}


def seed(reset=False):
    if reset:
        path = db.db_path()
        db.close_db()
        if os.path.exists(path):
            os.remove(path)
        db.init_db()
    if db.scalar("SELECT COUNT(*) FROM brands"):
        print("Brands already exist — skipping demo seed (use --reset to start over).")
        return
    rng = random.Random(7)
    created = (date.today() - timedelta(days=200)).isoformat()
    for spec in BRANDS:
        brand_id = db.insert("brands", {**spec, "created_at": created, "updated_at": db.now()})
        for name, pos, tiers, signals, x, y in COMPETITORS[spec["name"]]:
            db.insert("competitors", {"brand_id": brand_id, "name": name, "positioning": pos, "client_tiers": tiers,
                                      "signals": signals, "axis_x": x, "axis_y": y, "created_at": db.now()})
        archetypes = [a.split(":")[0] for a in spec["archetypes"].split("\n")]
        names = rng.sample([(f, l) for f in FIRST for l in LAST], 14)
        for first, last in names:
            country, city = rng.choice(PLACES)
            interests = rng.sample(CLUSTERS, rng.randint(2, 5))
            arch = rng.choice(archetypes)
            phase = rng.choice(PHASES)
            if arch.startswith("The Next-Gen") and rng.random() < .7:
                phase = rng.choice(["At risk", "Dormant"])
            cid = db.insert("clients", {
                "brand_id": brand_id, "name": f"{first} {last}", "email": f"{first.lower()}.{last.split()[0].lower()}@example.com",
                "country": country, "city": city, "tier": rng.choice(["Platinum", "VVIC", "Gold", "Top 100"]),
                "archetype": arch, "phase": phase,
                "engagement_score": rng.randint(15, 45) if phase in ("At risk", "Dormant") else rng.randint(45, 96),
                "lifetime_value": rng.choice([85, 120, 240, 380, 650, 1200, 2400]) * 1000,
                "interests": interests, "affinities": {i: rng.randint(40, 98) for i in interests},
                "social_circle": rng.sample(CIRCLES, rng.randint(1, 3)),
                "cross_purchases": ", ".join(rng.sample(PURCHASES, rng.randint(1, 3))),
                "behavioral_signals": rng.choice(SIGNALS), "social_footprint": rng.choice(
                    ["Private Instagram, 400 followers", "No public social presence", "Active on LinkedIn, speaks at conferences",
                     "Featured in Tatler 2025", "Family foundation website only"]),
                "notes": "Demo client (fictional).", "source": "demo", "created_at": created, "updated_at": db.now()})
            for k in range(rng.randint(1, 4)):
                db.insert("client_events", {"client_id": cid, "date": (date.today() - timedelta(days=rng.randint(5, 400))).isoformat(),
                                            "kind": rng.choice(["Purchase", "Visit", "Event", "Gift", "Message"]),
                                            "description": rng.choice(["Private viewing at the salon", "Anniversary gift for spouse",
                                                                       "Attended dinner in Geneva", "Thank-you note sent",
                                                                       "Bespoke enquiry", "Repair & service"])})
        for kind, title, summary, urg, imp, month, payload in ITEMS[spec["name"]]:
            db.insert("items", {"brand_id": brand_id, "scope": "brand", "kind": kind, "title": title, "summary": summary,
                                "urgency": urg, "impact": imp, "month": month, "payload": payload, "model": "demo-seed",
                                "brand_label": spec["name"], "status": "accepted" if kind == "initiative" else "proposed",
                                "created_at": db.now(), "updated_at": db.now()})
    for i, (rev, pipe, ret) in enumerate([(18, 60, 2), (22, 75, 2), (19, 90, 3), (31, 110, 3), (28, 140, 3), (36, 165, 4)]):
        period = (date.today().replace(day=1) - timedelta(days=31 * (5 - i))).strftime("%Y-%m")
        db.insert("kpis", {"period": period, "name": "Revenue", "value": rev * 1000, "unit": "€", "created_at": db.now()})
        db.insert("kpis", {"period": period, "name": "Pipeline value", "value": pipe * 1000, "unit": "€", "created_at": db.now()})
        db.insert("kpis", {"period": period, "name": "Active retainers", "value": ret, "unit": "#", "created_at": db.now()})
    db.insert("goals", {"title": "Sign 3 haute horlogerie retainers", "metric": "retainers", "target": 3, "current": 1,
                        "due": f"{date.today().year + 1}-06-30", "notes": "Independents first.", "created_at": db.now(), "updated_at": db.now()})
    db.insert("goals", {"title": "Publish the first Vestige Luxury Client Intelligence Report", "metric": "reports",
                        "target": 1, "current": 0, "due": f"{date.today().year + 1}-03-31", "created_at": db.now(), "updated_at": db.now()})
    print("Demo portfolio loaded: 2 fictional maisons, 28 clients, competitors, work items, KPIs and goals.")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        seed(reset="--reset" in sys.argv)
