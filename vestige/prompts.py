"""Prompt library and the registry of every kind of strategic work item.

Each entry in KINDS drives one generator: what context the model sees, what it
is asked to produce, which fields each item carries, and how the UI renders it.
Adding a new deliverable type is a matter of adding an entry here.
"""

INTEREST_CLUSTERS = [
    "Arts", "Travel", "Gastronomy", "Philanthropy", "Motorsport", "Real Estate",
    "Collectibles", "Wine & Spirits", "Wellness", "Fashion", "Sailing", "Equestrian",
    "Music", "Design & Architecture", "Investing", "Sport", "Family",
]
PHASES = ["Discovery", "Courtship", "Engaged", "Loyal", "Ambassador", "At risk", "Dormant"]
DEFAULT_ARCHETYPES = [
    "The Connoisseur", "The Collector", "The Heir", "The Self-Made Visionary",
    "The Cultural Patron", "The Discreet Traditionalist", "The Global Nomad", "The Next-Gen Tastemaker",
]

VESTIGE_SYSTEM = """You are the strategic intelligence engine of Vestige (vestigeloyalty.com), \
a relationship-strategy practice that helps luxury maisons build lasting, emotionally \
rooted relationships with high-net-worth clients (HNWI/UHNWI).

How you think:
- Like a senior partner in luxury clienteling and experiential design: relational, never transactional.
- Every recommendation must be anchored in the maison's heritage, codes and tone, and in observed client behaviour.
- Prefer the specific over the generic: name formats, moments, partners, rituals, cadences, owners.
- Quiet luxury: discretion, scarcity, cultural depth and personal recognition beat volume and spectacle.
- Be candid. If the data is thin or a direction would dilute brand equity, say so.
- Never invent facts about real, named people. Treat client data as confidential.

Output rules: respond with JSON only — no prose before or after, no markdown fences."""

# context: which builder in analytics.py feeds the prompt
# input:   optional free-text input shown next to the Generate button
# count:   default number of items requested
KINDS = {
    # ------------------------------------------------------------ brand ----
    "insight": {
        "label": "Insight", "plural": "Insight Feed", "scope": "brand", "context": "brand", "count": 6,
        "instruction": "Scan the whole client portfolio and surface the most important observations, "
                       "opportunities and risks right now. Rank by urgency and potential impact.",
        "fields": {
            "category": "one of: opportunity | risk | observation",
            "evidence": "the specific signals in the data that support this",
            "recommended_action": "the concrete next move, with owner and timing",
            "clients_concerned": "which clients / segments (names or archetypes)",
        },
        "input": "Optional focus (e.g. 'Q4 gifting season', 'Middle East clients')",
    },
    "prospect": {
        "label": "Analyst answer", "plural": "Ask the analyst", "scope": "brand", "context": "brand", "count": 1,
        "instruction": "Work autonomously on the strategic question below. Return a single structured analysis.",
        "fields": {
            "analysis": "the reasoning, 2-4 short paragraphs",
            "evidence": "list of data points from the portfolio supporting the conclusion",
            "recommendations": "list of prioritised recommendations",
            "next_actions": "list of concrete next actions with owner and timing",
            "confidence": "high | medium | low, with one line on why",
        },
        "input": "Your question — e.g. 'Which clients could become ambassadors in the next 6 months?'",
        "input_required": True,
    },
    "story": {
        "label": "Story arc", "plural": "Storytelling strategies", "scope": "brand", "context": "brand", "count": 3,
        "instruction": "Draft narrative strategies — story arcs, content themes and messaging angles — "
                       "filtered through the brand codes and the behavioural profile of the clients.",
        "fields": {
            "narrative_arc": "list of 3-5 acts/chapters of the story",
            "content_themes": "list of content themes",
            "messaging_angles": "list of messaging angles, written in the brand's tone of voice",
            "target_archetypes": "which client archetypes this speaks to",
            "channels": "where it lives (private salon, letter, film, dinner, app, advisor conversation...)",
            "heritage_anchor": "the heritage element it draws from",
        },
        "input": "Optional brief (e.g. 'anniversary of the founding atelier')",
    },
    "community": {
        "label": "Community blueprint", "plural": "Community blueprints", "scope": "brand", "context": "brand", "count": 2,
        "instruction": "Propose community-building initiatives built on belonging, trust and the brand's heritage — "
                       "communities clients would feel privileged to be part of.",
        "fields": {
            "concept": "the community idea in 2-3 sentences",
            "belonging_mechanism": "what makes members feel they belong",
            "rituals": "list of recurring rituals / moments",
            "membership_logic": "who is invited, how, and why it stays scarce",
            "heritage_link": "how it connects to the maison's heritage",
            "success_signals": "list of signals that it is working",
        },
    },
    "retention": {
        "label": "Retention play", "plural": "Retention by archetype", "scope": "brand", "context": "brand", "count": 4,
        "instruction": "Map the client base to behavioural archetypes and design tailored retention actions for each "
                       "archetype present (prioritise archetypes with at-risk or dormant clients).",
        "fields": {
            "archetype": "the archetype",
            "risk_signals": "behavioural signals that this archetype is drifting",
            "actions": "list of tailored retention actions",
            "cadence": "contact cadence and moments",
            "owner": "who owns it (client advisor, boutique director, CRM team...)",
        },
    },
    "initiative": {
        "label": "Experiential initiative", "plural": "Experiential initiatives", "scope": "brand", "context": "brand",
        "count": 6, "uses_month": True,
        "instruction": "Propose experiential initiatives (events, journeys, private moments) aligned with the brand "
                       "identity and the clients' interest clusters, spread across the next 12 months.",
        "fields": {
            "format": "format (private dinner, atelier visit, journey, salon, sporting moment...)",
            "month": "integer 1-12, month of the year it should happen",
            "interest_clusters": "interest clusters it activates",
            "target_archetypes": "archetypes it is designed for",
            "emotional_impact": "integer 1-5",
            "engagement_lift": "expected lift, short (e.g. '+15% repeat purchase among Collectors')",
            "guest_count": "indicative number of guests",
            "budget_band": "€ / €€ / €€€ / €€€€",
            "rationale": "why this, why now, why for these clients",
        },
        "input": "Optional constraint (e.g. 'budget under €80k', 'Gulf market')",
    },
    "collaboration": {
        "label": "Collaboration", "plural": "Collaboration pipeline", "scope": "brand", "context": "brand_competitors",
        "count": 6,
        "instruction": "From the clients' interest clusters, surface cross-industry partnerships (arts institutions, "
                       "hospitality, gastronomy, motorsport, yachting, galleries, foundations...). Run a brand-fit check "
                       "on each and avoid partners already associated with the listed competitors.",
        "fields": {
            "partner": "partner name or partner type",
            "category": "sector of the partner",
            "compatibility": "integer 0-100",
            "rationale": "why this partner fits these clients",
            "activation_idea": "the concrete activation",
            "brand_fit_check": "any misalignment that could dilute brand equity",
            "risk_level": "low | medium | high",
            "rival_conflict": "whether a competitor already claims this territory",
        },
        "input": "Optional sector focus",
    },
    "cx_map": {
        "label": "Touchpoint", "plural": "Emotional CX map", "scope": "brand", "context": "brand", "count": 8,
        "instruction": "Chart the client journey touchpoints end-to-end (from first encounter to after-care and "
                       "legacy) and propose enhancements that deepen emotional connection at each.",
        "fields": {
            "stage": "journey stage",
            "current_state": "how it likely works today",
            "enhancement": "the proposed enhancement",
            "target_emotion": "the emotion to evoke",
            "owner": "who owns the touchpoint",
        },
    },
    "event_design": {
        "label": "Event design", "plural": "Event emotion designer", "scope": "brand", "context": "brand", "count": 1,
        "instruction": "Design the experiential moment described below beat by beat, annotating each emotional beat "
                       "with the brand's tone and values.",
        "fields": {
            "guest_profile": "who it is for",
            "beats": "list of objects {moment, emotion, brand_cue}",
            "tone_notes": "tone, sensory and hospitality notes",
            "follow_up": "how the relationship continues after the event",
        },
        "input": "Describe the event (e.g. 'intimate dinner in Kyoto for 12 collectors')",
        "input_required": True,
    },
    "audit": {
        "label": "Strategy weakness", "plural": "Strategy audit", "scope": "brand", "context": "brand_competitors",
        "count": 6,
        "instruction": "Audit the brand's current relationship strategy. Detect weaknesses: misaligned messaging, "
                       "generic approaches, transactional vs relational gaps, community deficits, emotional "
                       "touchpoint voids, competitive vulnerabilities. Give pivot recommendations.",
        "fields": {
            "category": "messaging | generic approach | transactional gap | community deficit | emotional void | competitive vulnerability",
            "severity": "low | medium | high | critical",
            "rationale": "why this is a weakness, grounded in the data",
            "pivot": "the recommended pivot",
            "expected_impact": "expected impact if fixed",
            "next_steps": "list of next steps",
        },
        "input": "Optional: paste notes on the brand's current strategy",
    },
    "competitive": {
        "label": "Competitive read", "plural": "Competitive cross-examination", "scope": "brand",
        "context": "brand_competitors", "count": 0,
        "instruction": "Cross-examine the brand against EACH listed competitor across shared or similar client tiers. "
                       "One item per competitor.",
        "fields": {
            "competitor": "competitor name",
            "shared_tiers": "client tiers they compete for",
            "affinity_overlap": "interest clusters where they overlap with our clients",
            "engagement_gaps": "where the competitor engages better or worse",
            "whitespace": "list of whitespace opportunities",
            "threats": "list of threats by interest category",
            "threat_level": "low | medium | high",
        },
    },
    # --------------------------------------------------------- internal ----
    "brief": {
        "label": "Intelligence brief", "plural": "Intelligence briefs", "scope": "internal", "context": "internal",
        "count": 1,
        "instruction": "Write an Intelligence Brief on the state of luxury client behaviour and brand relationship "
                       "strategy, based on the anonymised cross-brand data. Draw conclusions and detect opportunities.",
        "fields": {
            "key_findings": "list of key findings with numbers",
            "implications": "list of implications for luxury maisons",
            "opportunities": "list of opportunities detected",
            "methodology_note": "one sentence on data basis and limits",
        },
        "input": "Optional theme (e.g. 'Next-gen heirs and experiential formats')",
    },
    # ----------------------------------------------------------- growth ----
    "growth_plan": {
        "label": "Growth move", "plural": "Growth action plan", "scope": "growth", "context": "growth", "count": 8,
        "instruction": "Analyse the body of work across engagements and diagnostics, the proactive prospect pipeline, "
                       "and Vestige's KPIs and goals. Produce a "
                       "prioritised, step-by-step growth action plan for scaling Vestige, covering: sectors to target "
                       "next (where intelligence shows the biggest retention gaps), services to package (repeated "
                       "client needs), partnership/referral networks, thought-leadership and intelligence-report "
                       "publishing, pricing and packaging, geographic expansion.",
        "fields": {
            "horizon": "0-3 months | 3-6 months | 6-12 months",
            "area": "sector targeting | service packaging | partnerships | thought leadership | pricing | geography",
            "actions": "list of concrete steps",
            "kpi": "how success is measured",
            "expected_outcome": "expected business outcome (revenue, pipeline, positioning)",
        },
    },
    "radar": {
        "label": "Market opportunity", "plural": "Market opportunity radar", "scope": "growth", "context": "growth",
        "count": 5,
        "instruction": "Scan the internal intelligence layer for new business opportunities for Vestige — patterns "
                       "across engagements that reveal underserved sectors, markets or needs.",
        "fields": {
            "sector": "sector or market",
            "signal": "the pattern observed across engagements",
            "evidence": "data supporting it",
            "service_fit": "which Vestige service answers it",
            "estimated_value": "indicative commercial value",
            "confidence": "high | medium | low",
        },
        "input": "Optional external signals you've noticed",
    },
    "health_check": {
        "label": "Practice finding", "plural": "Practice health check", "scope": "growth", "context": "growth",
        "count": 5,
        "instruction": "Audit Vestige's own practice: engagement velocity, client satisfaction signals, deliverable "
                       "quality patterns and strategic blind spots in how Vestige positions itself.",
        "fields": {
            "dimension": "velocity | satisfaction | deliverable quality | positioning | capacity",
            "assessment": "the honest assessment",
            "rating": "integer 1-5 (5 = excellent)",
            "recommendation": "what to change",
        },
    },
    "vestige_ip": {
        "label": "IP & service move", "plural": "Vestige IP & service optimisation", "scope": "growth",
        "context": "growth", "count": 6,
        "instruction": "Using the patterns across ALL client diagnostics (archetypes, weaknesses, opportunities, "
                       "reallocations) and the proactive pipeline (problem signals seen in prospects), recommend how "
                       "Vestige should strengthen its intellectual property and its service: a proprietary archetype "
                       "framework that generalises across maisons, productised service modules and price points, "
                       "methodology and data improvements, benchmarks and reports Vestige can own and publish, and "
                       "the company direction these patterns point to.",
        "fields": {
            "type": "IP asset | service module | methodology | pricing | direction",
            "pattern_evidence": "the cross-client or pipeline pattern this is built on",
            "proposal": "what to build or change",
            "how_to_build": "list of concrete steps",
            "commercial_effect": "effect on revenue, margin, differentiation or pipeline",
        },
    },
    "course_correction": {
        "label": "Course correction", "plural": "Goal course corrections", "scope": "growth", "context": "growth",
        "count": 0,
        "instruction": "For EACH active growth goal, assess progress versus target and timeline, and suggest a course "
                       "correction. One item per goal.",
        "fields": {
            "goal": "the goal",
            "diagnosis": "on track / behind / ahead and why",
            "correction": "the course correction",
            "next_steps": "list of next steps",
        },
    },
}

SECTIONS = {
    # page -> kinds rendered on it
    "insights": ["insight", "prospect"],
    "studio": ["story", "community"],
    "retention": ["retention", "initiative"],
    "collaborations": ["collaboration"],
    "emotion": ["cx_map", "event_design", "audit"],
    "competitors": ["competitive"],
}


def item_prompt(kind, context, extra="", count=None):
    spec = KINDS[kind]
    n = count if count is not None else spec["count"]
    fields = "\n".join(f'    "{k}": {v}' for k, v in spec["fields"].items())
    how_many = f"Return exactly {n} item(s)." if n else "Return one item per entity as instructed."
    extra_block = f"\n\n## Brief from Vestige\n{extra.strip()}" if extra and extra.strip() else ""
    return f"""{context}

## Task
{spec['instruction']}{extra_block}

## Output format
Return a JSON object: {{"items": [ ... ]}}. {how_many}
Each item has:
    "title": a short, editorial headline (max 10 words),
    "summary": 1-3 sentences, the "so what",
    "urgency": integer 1-5,
    "impact": integer 1-5,
{fields}
"""


DISCOVERY_PROMPT = """{context}

## Task
Vestige has gathered the raw notes below on a client. Organise them into a structured
behavioural profile. Only use what the notes support; list what is missing as info gaps.
Interest clusters must come from: {clusters}.
Phase must be one of: {phases}.

## Raw notes
{notes}

## Output format
Return JSON:
{{"name": str, "email": str, "country": str, "city": str, "tier": str,
  "archetype": str (prefer the brand's archetypes: {archetypes}),
  "phase": str, "engagement_score": int 0-100, "lifetime_value": number (EUR, 0 if unknown),
  "interests": [cluster, ...], "affinities": {{cluster: int 0-100}},
  "social_circle": [people/institutions/clubs mentioned],
  "social_footprint": str, "cross_purchases": str, "behavioral_signals": str,
  "info_gaps": str (bullet-like list of missing information worth collecting),
  "summary": str (2 sentences, the relationship opportunity)}}
"""

CLIENT_GAPS_PROMPT = """{context}

## Client
{client}

## Task
Review this client profile. Identify missing information worth collecting (and how to collect it
discreetly), patterns worth acting on, and the next best relationship move.

## Output format
Return JSON: {{"info_gaps": [str], "patterns": [str], "next_best_action": str}}
"""

DECK_PROMPT = """{context}

## Task
Compose a client-ready presentation for "{title}" (audience: {audience}) from the work below.
Write in Vestige's voice: editorial, precise, warm, never salesy. Open with an executive summary,
group the work into a clear storyline, end with next steps. 8-14 slides.

## Source work
{work}

## Output format
Return JSON: {{"slides": [ ... ]}} where each slide is one of:
  {{"type": "cover", "title": str, "subtitle": str}}
  {{"type": "section", "title": str, "subtitle": str}}
  {{"type": "text", "title": str, "body": str, "bullets": [str]}}
  {{"type": "metrics", "title": str, "metrics": [{{"label": str, "value": str}}]}}
  {{"type": "quote", "title": str, "body": str}}
  {{"type": "closing", "title": str, "bullets": [str]}}
"""
