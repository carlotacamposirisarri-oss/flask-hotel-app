"""Fictional behavioural personas used to generate a realistic demo CRM, plus a
hand-written demo diagnostic and demo prospect so the deliverables can be seen
before any API key is connected. Everything here is invented and stamped demo."""

PERSONAS = {
    "Maison Aurèle": [
        {"key": "patron", "weight": 16, "interests": ["Arts", "Philanthropy", "Music", "Design & Architecture"],
         "cross": ["Contemporary African art", "Christie's evening sale lots", "Hasselblad archive prints"],
         "cats": ["High Jewellery", "Archive Re-editions"], "ltv": (300, 900), "orders": (3, 7), "recency": (40, 200),
         "phases": ["Engaged", "Loyal", "Loyal", "Ambassador"], "places": [("France", "Paris"), ("UK", "London"), ("USA", "New York")],
         "signals": ["Engages with archive stories, ignores product launches", "Sits on two museum boards",
                     "Asked to see the gouache drawings behind her necklace"]},
        {"key": "heir", "weight": 14, "interests": ["Family", "Travel", "Equestrian", "Real Estate"],
         "cross": ["Hermès Kelly collection", "Aman residences", "Bugatti Chiron", "Private island villa"],
         "cats": ["High Jewellery", "Bridal", "Gifting"], "ltv": (900, 2600), "orders": (4, 10), "recency": (90, 330),
         "phases": ["Engaged", "Loyal", "At risk"], "places": [("UAE", "Dubai"), ("Saudi Arabia", "Riyadh"), ("Qatar", "Doha")],
         "signals": ["Buys for weddings and births, rarely for herself", "Visits only during Paris summer stay",
                     "Follows competitor's Biennale programme closely"]},
        {"key": "nextgen", "weight": 18, "interests": ["Fashion", "Music", "Wellness", "Design & Architecture"],
         "cross": ["Loro Piana bespoke", "Hasselblad archive prints"],
         "cats": ["Fine Jewellery", "Fragrance"], "ltv": (25, 110), "orders": (1, 2), "recency": (300, 700),
         "phases": ["Dormant", "At risk", "At risk", "Courtship"], "places": [("China", "Shanghai"), ("Hong Kong", "Hong Kong"), ("USA", "Los Angeles"), ("UK", "London")],
         "signals": ["Bought once at a launch, never returned", "Engages on Instagram, ignores emails",
                     "Asked about the atelier's craftspeople"]},
        {"key": "collector", "weight": 12, "interests": ["Sailing", "Collectibles", "Wine & Spirits", "Gastronomy"],
         "cross": ["Riva Aquariva", "Patek Philippe Nautilus", "Château Margaux en primeur"],
         "cats": ["High Jewellery", "Bespoke Commissions", "Watches"], "ltv": (650, 1500), "orders": (6, 14), "recency": (20, 120),
         "phases": ["Loyal", "Ambassador", "Ambassador"], "places": [("Monaco", "Monaco"), ("Switzerland", "Geneva"), ("Italy", "Milan")],
         "signals": ["Referred two friends in 2025", "Interested in bespoke commissions",
                     "Prefers private appointments on the yacht"]},
    ],
    "Vauclain Genève": [
        {"key": "connoisseur", "weight": 16, "interests": ["Collectibles", "Design & Architecture", "Music"],
         "cross": ["Patek Philippe Nautilus", "Hasselblad archive prints"], "cats": ["Minute Repeaters", "Perpetual Calendars"],
         "ltv": (240, 700), "orders": (3, 8), "recency": (60, 260), "phases": ["Engaged", "Loyal", "At risk"],
         "places": [("Switzerland", "Geneva"), ("Japan", "Tokyo"), ("Singapore", "Singapore")],
         "signals": ["Waited 26 months for allocation", "Asks to meet the watchmaker"]},
        {"key": "founder", "weight": 14, "interests": ["Motorsport", "Sailing", "Investing"], "cross": ["Ferrari SF90", "Riva Aquariva"],
         "cats": ["Sports Complications"], "ltv": (120, 380), "orders": (1, 3), "recency": (150, 500),
         "phases": ["Courtship", "Engaged", "At risk", "Dormant"], "places": [("USA", "New York"), ("USA", "Los Angeles"), ("UK", "London")],
         "signals": ["Bought a Hartmann & Söhne chronograph last year", "Time-poor; prefers concierge"]},
        {"key": "traditionalist", "weight": 12, "interests": ["Family", "Equestrian", "Wine & Spirits"],
         "cross": ["Château Margaux en primeur", "Racehorse share"], "cats": ["Pocket Watches", "Perpetual Calendars"],
         "ltv": (650, 2400), "orders": (4, 9), "recency": (30, 180), "phases": ["Loyal", "Ambassador"],
         "places": [("Switzerland", "Zurich"), ("Germany", "Munich"), ("France", "Paris")],
         "signals": ["Family has owned Vauclain for three generations", "Avoids any public event"]},
    ],
}

DEMO_STRATEGY = {
    "Maison Aurèle": {
        "current_strategy": "Annual calendar built around two high-jewellery launches (Paris couture week, Dubai). "
                            "Champagne cocktails and photo walls in boutiques; seasonal gifting to top 200 clients; CRM "
                            "emails every two weeks; Biennale sponsorship stopped in 2024. Clienteling sits with four "
                            "senior advisors; no structured after-purchase journey; KPIs tracked: sell-through at launches.",
        "resource_allocation": "Launch events: 40%\nFashion-week presence: 20%\nGifting: 15%\nCRM & email: 10%\n"
                               "Private dinners: 10%\nArchive & heritage programmes: 5%",
    },
    "Vauclain Genève": {
        "current_strategy": "Allocation list managed by boutique directors; one owners' dinner a year in Geneva; "
                            "presence at Watches & Wonders; no owners' community; US served from New York boutique only.",
        "resource_allocation": "Trade fairs: 45%\nBoutique events: 25%\nGifting: 10%\nManufacture visits: 10%\nDigital: 10%",
    },
}

COMPETITOR_ACTIONS = {
    "Orsini Gioielli": "2026: celebrity-led launch in Riyadh; Met Gala dressing; new 'Orsini Circle' app with points.",
    "Lumière de Seine": "2025-26: Venice Biennale pavilion sponsorship; private art-foundation dinners for VVICs; "
                        "acquired a stake in a contemporary gallery.",
    "Atelier Kōyō": "2026: Kyoto ceramic residency open to 20 collectors a year; quiet-luxury pop-up in Doha.",
    "Hartmann & Söhne": "Owners' club with track days; 2026 Le Mans hospitality; NYC owners' lounge opened.",
    "Maison Delorme": "Record auction result promoted heavily; invitation-only grande complication salon in Shanghai.",
    "Kessler Independent": "Instagram-first drops; collaboration with a design fair in Miami.",
}

# Written in the same JSON shape the AI returns, keyed by persona.
DEMO_ARCHETYPES = {
    "patron": {"name": "The Cultural Patron", "essence": "Buys meaning, not stones: each piece must carry a story worth telling at a museum dinner.",
               "defining_behaviours": ["Arts appears in nearly every profile of the segment", "Strongest cross-purchase lift in art and auctions",
                                       "Mid-high value with steady repeat purchases"],
               "motivations": ["Cultural legitimacy", "Being an insider to creation"], "emotional_drivers": ["Discovery", "Belonging to a circle of taste"],
               "relationship_to_brand": "Responds to the archive and the lapidary's craft; bored by launches.",
               "commercial_role": "Stable revenue and the maison's best ambassadors to new collectors.",
               "risk_signals": ["Follows Lumière de Seine's art programme"], "data_caveats": "Interests are advisor-entered."},
    "heir": {"name": "The Dynastic Gifter", "essence": "Marks family milestones with jewellery; loyal to rituals, not to brands.",
             "defining_behaviours": ["Highest average lifetime value of all segments", "Purchases cluster around bridal and gifting",
                                     "Long gaps between visits, concentrated in summer"],
             "motivations": ["Continuity", "Recognition of the family"], "emotional_drivers": ["Pride", "Ceremony"],
             "relationship_to_brand": "Trusts one advisor; experiences the maison only through launches in Dubai.",
             "commercial_role": "Largest share of value — and the most exposed to Orsini's Riyadh push.",
             "risk_signals": ["Rising share of at-risk relationships", "Competitor events attended"], "data_caveats": "Family relationships are under-documented."},
    "nextgen": {"name": "The Seeking Newcomer", "essence": "Arrived through a launch, looking for a reason to stay that the maison never gave.",
                "defining_behaviours": ["Largest segment by headcount, smallest by value", "Typically one purchase, long ago",
                                        "Majority dormant or at risk"],
                "motivations": ["Self-expression", "Access to makers"], "emotional_drivers": ["Curiosity", "Authenticity"],
                "relationship_to_brand": "Transactional by design: bought at a launch, then received generic emails.",
                "commercial_role": "Future value pipeline; currently a leak.", "risk_signals": ["Ignores email; engages on Instagram"],
                "data_caveats": "Low purchase history makes the segment noisier."},
    "collector": {"name": "The Sea-Going Collector", "essence": "Collects across categories with a connoisseur's patience and a sailor's calendar.",
                  "defining_behaviours": ["Highest purchase frequency", "Most recent purchases of all segments",
                                          "Strong cross-purchases in yachting, watches and wine"],
                  "motivations": ["Mastery", "Rarity"], "emotional_drivers": ["Anticipation", "Craft intimacy"],
                  "relationship_to_brand": "Best-served segment: private appointments and bespoke commissions.",
                  "commercial_role": "Bespoke revenue engine and referral source.", "risk_signals": ["Few — protect, do not over-invite"],
                  "data_caveats": "Small segment."},
}


def demo_crossexam(names):
    p, h, n, c = (names.get(k, k) for k in ("patron", "heir", "nextgen", "collector"))
    return {
        "matrix": [
            {"archetype": p, "identity_fit": 92, "strategy_coverage": 25, "competitor_pressure": 80, "main_competitor": "Lumière de Seine", "reading": "Perfect fit with the archive, almost ignored since the Biennale exit."},
            {"archetype": h, "identity_fit": 70, "strategy_coverage": 45, "competitor_pressure": 85, "main_competitor": "Orsini Gioielli", "reading": "Served only through launches while Orsini courts them at home."},
            {"archetype": n, "identity_fit": 65, "strategy_coverage": 10, "competitor_pressure": 55, "main_competitor": "Atelier Kōyō", "reading": "Recruited by launches, then abandoned."},
            {"archetype": c, "identity_fit": 88, "strategy_coverage": 80, "competitor_pressure": 30, "main_competitor": "—", "reading": "Well served; risk of over-solicitation."},
        ],
        "weaknesses": [
            {"title": "60% of the budget funds launches that recruit clients who never return", "evidence": f"{n} is the largest segment and mostly dormant; launches and fashion weeks take 60% of spend.", "archetypes": [n], "severity": "critical", "cost_of_inaction": "Acquisition cost written off every season."},
            {"title": "The maison's richest asset — the archive — gets 5%", "evidence": f"{p} over-indexes on arts and responds to heritage; archive programmes receive 5%.", "archetypes": [p], "severity": "high", "cost_of_inaction": "Cultural Patrons drift to Lumière de Seine's foundation dinners."},
            {"title": "Gulf families experience the maison only at launches", "evidence": f"{h} holds the largest value share with rising risk; Orsini launched in Riyadh in 2026.", "archetypes": [h], "severity": "high", "cost_of_inaction": "Loss of the most valuable relationships."},
            {"title": "No after-purchase journey", "evidence": "No structured follow-up after first purchase; CRM is generic bi-weekly email.", "archetypes": [n, h], "severity": "medium", "cost_of_inaction": "Repeat rate stays low."},
        ],
        "opportunities": [
            {"title": "Turn the gouache archive into a private cultural programme", "evidence": "Unique, uncopiable asset; Patrons' highest lift is arts.", "archetypes": [p, c], "value_at_stake": "High — protect largest referral source", "why_we_win": "No rival owns 40,000 original drawings."},
            {"title": "Family ceremonies hosted in the Gulf, not launches", "evidence": "Gifter purchases cluster around milestones.", "archetypes": [h], "value_at_stake": "Very high — largest value share", "why_we_win": "Aurèle's poetry suits rites of passage better than Orsini's spectacle."},
            {"title": "An apprenticeship journey for newcomers", "evidence": "Newcomers ask about makers and craft.", "archetypes": [n], "value_at_stake": "Medium now, high in 5 years", "why_we_win": "Craft intimacy is authentic to the maison."},
        ],
        "competitor_reads": [
            {"competitor": "Orsini Gioielli", "what_they_do_well": "Visibility and presence in the Gulf", "where_they_are_weak": "Spectacle without intimacy", "archetypes_targeted": [h, n]},
            {"competitor": "Lumière de Seine", "what_they_do_well": "Art-world access", "where_they_are_weak": "Group-owned, less personal", "archetypes_targeted": [p]},
        ],
        "synthesis": "The maison spends most of its relationship budget on launches that recruit clients it then loses, while its two most valuable archetypes are courted at home by competitors. Its unfair advantage — the archive and the lapidary's craft — is almost unused.",
    }


def demo_strategy(names):
    p, h, n, c = (names.get(k, k) for k in ("patron", "heir", "nextgen", "collector"))
    return {
        "headline": "From launch spectacle to the intimacy of the atelier: fund fewer, deeper rituals around the archive.",
        "executive_summary": [
            "Four behavioural archetypes, not the generic VIC tiers, explain who creates value.",
            f"{h} and {p} hold most of the value and are under-served while competitors court them.",
            "Launch events absorb 40% of the budget and mainly recruit one-time buyers.",
            "Redirect a quarter of the budget from launches and fashion weeks to an archive-led cultural programme and family ceremonies.",
            "Measure emotion (invitations accepted, referrals, stories retold) alongside repeat purchase and bespoke revenue.",
        ],
        "north_star": {"concept": "Les Heures de l'Atelier — the maison opens its archive and its bench to the families and patrons who carry its stories.", "why_it_is_ownable": "Built on 40,000 original gouaches and a named lapidary lineage no competitor can claim."},
        "reallocation": [
            {"from": "Launch events", "to": "Archive & heritage programme", "shift_pct": 15, "rationale": "Patrons and Collectors respond to heritage; launches recruit churners."},
            {"from": "Fashion-week presence", "to": "Gulf family ceremonies", "shift_pct": 10, "rationale": "Meet the largest value pool where Orsini is attacking."},
            {"from": "CRM & email", "to": "Newcomer apprenticeship journey", "shift_pct": 5, "rationale": "Replace generic email with a 90-day journey."},
        ],
        "target_allocation": [{"line": "Archive & heritage programme", "pct": 20}, {"line": "Gulf family ceremonies", "pct": 20},
                              {"line": "Launch events", "pct": 25}, {"line": "Private dinners", "pct": 15},
                              {"line": "Gifting", "pct": 10}, {"line": "Newcomer journey", "pct": 5}, {"line": "Fashion-week presence", "pct": 5}],
        "archetype_plays": [
            {"archetype": p, "objective": "Re-anchor patrons in the maison's culture", "experiential_pillar": "The living archive", "cadence": "Quarterly, 12 guests",
             "signature_experiences": [{"name": "Gouache Nights", "format": "After-hours salon", "description": "Original drawings beside the stones they inspired.", "emotional_impact": 5, "commercial_kpi": "Bespoke enquiries", "expected_result": "+20% within 12 months"}]},
            {"archetype": h, "objective": "Own the family milestones", "experiential_pillar": "Ceremonies of transmission", "cadence": "On request + 2 hosted moments a year",
             "signature_experiences": [{"name": "The First Jewel", "format": "Private ceremony at home", "description": "A lapidary travels to present a child's first piece.", "emotional_impact": 5, "commercial_kpi": "Retention of at-risk families", "expected_result": "Halve at-risk share"}]},
            {"archetype": n, "objective": "Convert first buyers into second purchases", "experiential_pillar": "Apprenticeship", "cadence": "90-day journey after first purchase",
             "signature_experiences": [{"name": "A Morning at the Bench", "format": "Atelier visit", "description": "Set a stone beside a craftsperson.", "emotional_impact": 4, "commercial_kpi": "Second-purchase rate", "expected_result": "From ~10% to 25%"}]},
            {"archetype": c, "objective": "Protect and deepen", "experiential_pillar": "Commission journeys", "cadence": "As commissions progress",
             "signature_experiences": [{"name": "Stone hunting", "format": "Private sourcing trip", "description": "Join the gemmologist to choose a stone.", "emotional_impact": 5, "commercial_kpi": "Bespoke revenue", "expected_result": "+15%"}]},
        ],
        "roadmap": [{"quarter": "Q1", "initiatives": ["Archive digitisation for salons", "Design the newcomer journey"]},
                    {"quarter": "Q2", "initiatives": ["First Gouache Night (Paris)", "Pilot ceremonies with 5 Gulf families"]},
                    {"quarter": "Q3", "initiatives": ["Venice: patrons' journey", "Scale newcomer journey"]},
                    {"quarter": "Q4", "initiatives": ["Ceremonies in Riyadh and Doha", "Review KPIs and re-allocate"]}],
        "kpis": {"emotional": ["Invitation acceptance rate", "Referrals per archetype", "Stories retold (advisor log)"],
                 "commercial": ["Repeat-purchase rate", "Bespoke revenue", "At-risk value recovered"]},
        "quick_wins": ["Stop generic bi-weekly emails for dormant newcomers", "Invite 12 patrons to an archive preview",
                       "Assign each at-risk Gulf family a ceremony owner"],
        "assumptions": ["Budget stays flat", "Archive can be shown privately", "Figures are illustrative (demo data)"],
    }


DEMO_PROSPECT = {
    "company": "Maison Solenne (fictional demo)", "sector": "Haute joaillerie", "market": "Europe, GCC", "website": "",
    "why": "Fictional example lead — shows what a researched dossier and pitch look like.",
    "dossier": {
        "snapshot": {"positioning": "Parisian joaillier repositioning towards 'quiet luxury'", "heritage": "Founded 1923; art-deco archive",
                     "markets": "France, UAE, Saudi Arabia", "scale_signals": "12 boutiques; new Riyadh flagship announced",
                     "leadership_priorities": "CEO interview: 'clienteling is our next frontier'"},
        "initiatives": [{"initiative": "Riyadh flagship opening", "date": "2026-05", "type": "opening", "source": ""},
                        {"initiative": "Celebrity-led capsule launch", "date": "2026-02", "type": "launch", "source": ""}],
        "client_signals": [{"signal": "Interviews mention 'younger Gulf clients' as the growth target", "source": ""}],
        "competitors": [{"name": "Orsini Gioielli", "recent_actions": "Riyadh launch and points-based app", "source": ""}],
        "claims_and_reports": [{"claim": "We want every client to feel like family", "who": "CEO", "date": "2026", "source": ""}],
        "sentiment": {"summary": "Admiration for design; complaints about after-sales and waiting times.", "themes": ["after-sales", "waitlists", "design"], "sources": []},
        "problem_signals": [
            {"signal": "Launch-driven calendar", "evidence": "Three launches in 12 months, no owner programme", "source": "", "problem_type": "generic experiences", "severity": "high", "fact_or_inference": "inference"},
            {"signal": "After-sales complaints in public reviews", "evidence": "Recurring theme in reviews", "source": "", "problem_type": "retention", "severity": "medium", "fact_or_inference": "inference"},
        ],
        "likely_archetypes": [{"name": "Gulf next-gen heirs", "rationale": "Stated growth target"}, {"name": "Parisian art-deco collectors", "rationale": "Archive-led pieces"}],
        "caveats": "Fictional demo dossier — no real company.",
    },
    "pitch": {
        "fit_score": 82, "fit_rationale": "Leadership names clienteling as a priority while the calendar remains launch-driven.",
        "timing": "Six months before the Riyadh flagship opens: the relationship strategy can still shape it.",
        "the_problem": "Solenne is opening in Riyadh with a launch playbook, while the clients it wants to win buy rituals, not events.",
        "opportunity_hypotheses": [{"hypothesis": "Design the Riyadh opening as a family-ritual programme", "evidence": "Gulf heirs as stated target", "vestige_answer": "Engagement Diagnostic + experiential strategy for the opening", "value": "Retention of first-year Riyadh clients"}],
        "pitch": {"angle": "From opening night to opening chapter", "hook": "Your Riyadh clients will remember the ceremony, not the launch.",
                  "proof_points": ["Archetype-led diagnostics across luxury maisons", "Experiential strategies built on heritage codes"],
                  "entry_offer": "An 8-week Engagement Diagnostic on the existing GCC client base, delivered before the opening.",
                  "objections": [{"objection": "We already have a CRM team", "response": "We make their data speak in archetypes and experiences — we don't replace them."}]},
        "decision_makers": ["Chief Client Officer", "Managing Director Middle East"],
        "outreach": {"email_subject": "Riyadh — the ceremony, not the launch",
                     "email_body": "Dear …,\n\nYour recent interview on clienteling as Solenne's next frontier resonated with what we see across maisons opening in the Gulf: the clients who matter most remember rituals, not launches.\n\nVestige helps maisons turn their client data into archetypes and design experiences around them. With Riyadh opening in May, there is a window to shape the first year of relationships.\n\nWould a 30-minute conversation in the coming weeks be useful?\n\nWarm regards,",
                     "linkedin_note": "Your view on clienteling as the next frontier struck a chord — I'd love to share what we see in Gulf openings.",
                     "follow_up": "Send a one-page archetype hypothesis for the Riyadh opening."},
        "next_steps": ["Validate decision maker", "Send email", "Prepare one-page hypothesis"],
    },
}
