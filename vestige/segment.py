"""Behavioural segmentation of a maison's client base.

Deterministic and reproducible: every client becomes a feature vector
(interest clusters, cross-industry purchases, own-brand categories, value,
frequency, recency, engagement); k-means++ groups them; k is chosen by
silhouette score. The AI only *interprets* the resulting segments — it never
invents them — so archetypes are traceable back to the data.
"""
import math
import re
from collections import Counter
from datetime import date, datetime

import numpy as np

AT_RISK = {"At risk", "Dormant"}
LOYAL = {"Loyal", "Ambassador"}

# Free-text cross-industry purchases -> comparable categories.
CROSS_INDUSTRY = {
    "Yachting": ["yacht", "riva", "sunseeker", "boat", "sailing", "aquariva"],
    "Automotive": ["ferrari", "bugatti", "porsche", "lamborghini", "rolls", "bentley", "aston", "mclaren", "car", "sf90", "chiron"],
    "Watches": ["patek", "rolex", "audemars", "vacheron", "watch", "nautilus", "tourbillon", "richard mille"],
    "Jewellery": ["cartier", "van cleef", "bulgari", "tiffany", "graff", "jewel", "diamond"],
    "Fashion & leather": ["hermès", "hermes", "chanel", "dior", "loro piana", "kelly", "birkin", "brioni", "couture", "bespoke"],
    "Art & collectibles": ["art", "gallery", "painting", "sculpture", "print", "auction", "christie", "sotheby", "archive"],
    "Wine & spirits": ["wine", "château", "chateau", "margaux", "petrus", "whisky", "cognac", "champagne", "en primeur"],
    "Hospitality & travel": ["aman", "hotel", "resort", "villa", "island", "jet", "cruise", "safari"],
    "Real estate": ["residence", "property", "penthouse", "estate", "real estate"],
    "Equestrian & sport": ["horse", "racehorse", "polo", "golf", "equestrian"],
    "Aviation": ["aviation", "netjets", "gulfstream", "private jet"],
}

DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d.%m.%Y", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S", "%b %d, %Y", "%d %b %Y")


def parse_date(v):
    s = str(v or "").strip()
    if not s:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s[:len(datetime.now().strftime(fmt))] if "%H" not in fmt else s, fmt).date()
        except ValueError:
            continue
    m = re.match(r"(\d{4})-(\d{2})", s)
    if m:
        return date(int(m.group(1)), int(m.group(2)), 1)
    return None


def cross_categories(text):
    low = str(text or "").lower()
    return sorted({cat for cat, words in CROSS_INDUSTRY.items() if any(w in low for w in words)})


def _recency_days(c, today):
    d = parse_date(c.get("last_purchase"))
    if d:
        return max(0, (today - d).days)
    # No purchase date in the CRM: approximate from lifecycle phase.
    return {"Ambassador": 60, "Loyal": 120, "Engaged": 200, "Courtship": 300, "Discovery": 365,
            "At risk": 450, "Dormant": 720}.get(c.get("phase"), 365)


def _kmeans(X, k, seed, iters=100):
    rng = np.random.default_rng(seed)
    n = len(X)
    centers = [X[rng.integers(n)]]
    for _ in range(1, k):  # k-means++ initialisation
        d2 = np.min(((X[:, None, :] - np.array(centers)[None]) ** 2).sum(-1), axis=1)
        probs = d2 / d2.sum() if d2.sum() > 0 else np.full(n, 1 / n)
        centers.append(X[rng.choice(n, p=probs)])
    C = np.array(centers)
    labels = np.zeros(n, dtype=int)
    for _ in range(iters):
        new = np.argmin(((X[:, None, :] - C[None]) ** 2).sum(-1), axis=1)
        if np.array_equal(new, labels) and _ > 0:
            break
        labels = new
        for j in range(k):
            if np.any(labels == j):
                C[j] = X[labels == j].mean(0)
    inertia = float(((X - C[labels]) ** 2).sum())
    return labels, inertia


def _silhouette(X, labels):
    k = labels.max() + 1
    if k < 2:
        return 0.0
    D = np.sqrt(((X[:, None, :] - X[None]) ** 2).sum(-1))
    scores = []
    for i in range(len(X)):
        same = labels == labels[i]
        if same.sum() <= 1:
            scores.append(0.0)
            continue
        a = D[i, same].sum() / (same.sum() - 1)
        b = min(D[i, labels == j].mean() for j in range(k) if j != labels[i] and np.any(labels == j))
        scores.append((b - a) / max(a, b) if max(a, b) > 0 else 0.0)
    return float(np.mean(scores))


def segment(clients, k=None, today=None):
    """Return {"assignments": {client_id: segment}, "segments": [...], "quality": {...}}."""
    today = today or date.today()
    n = len(clients)
    if n < 6:
        raise ValueError("At least 6 clients are needed to detect behavioural patterns.")

    interests = sorted({i for c in clients for i in c["interests"]})
    cross = [cross_categories(c.get("cross_purchases")) for c in clients]
    cross_vocab = sorted({x for row in cross for x in row})
    own = sorted({x for c in clients for x in (c.get("purchase_categories") or [])})

    def onehot(values, vocab):
        return [1.0 if v in values else 0.0 for v in vocab]

    numeric = np.array([[math.log1p(c["lifetime_value"] or 0), math.log1p(c.get("purchase_count") or 0),
                         _recency_days(c, today), c["engagement_score"] or 0] for c in clients], dtype=float)
    std = numeric.std(0)
    std[std == 0] = 1
    numeric = (numeric - numeric.mean(0)) / std
    # Weights: behaviour (value/frequency/recency/engagement) and passions carry most of the signal.
    X = np.hstack([
        np.array([onehot(c["interests"], interests) for c in clients]) * 1.0,
        np.array([onehot(row, cross_vocab) for row in cross]) * 0.8 if cross_vocab else np.zeros((n, 0)),
        np.array([onehot(c.get("purchase_categories") or [], own) for c in clients]) * 0.6 if own else np.zeros((n, 0)),
        numeric * 0.9,
    ])

    candidates = [k] if k else list(range(3, max(3, min(7, n // 4)) + 1))
    best = None
    for kk in candidates:
        runs = [_kmeans(X, kk, seed) for seed in range(8)]
        labels, _ = min(runs, key=lambda r: r[1])
        if len(set(labels)) < kk:
            continue
        sil = _silhouette(X, labels)
        if best is None or sil > best[1]:
            best = (labels, sil, kk)
    if best is None:
        labels, sil, kk = np.zeros(n, dtype=int), 0.0, 1
    else:
        labels, sil, kk = best

    # Order segments by total value so "Segment 1" is always the most valuable.
    totals = {j: sum(clients[i]["lifetime_value"] or 0 for i in range(n) if labels[i] == j) for j in range(kk)}
    order = {old: new for new, old in enumerate(sorted(totals, key=lambda j: -totals[j]))}
    labels = np.array([order[j] for j in labels])

    total_value = sum(c["lifetime_value"] or 0 for c in clients) or 1
    overall_interest = Counter(i for c in clients for i in c["interests"])
    overall_cross = Counter(x for row in cross for x in row)
    segments = []
    for j in range(kk):
        idx = [i for i in range(n) if labels[i] == j]
        members = [clients[i] for i in idx]
        m = len(members)
        seg_interest = Counter(i for c in members for i in c["interests"])
        seg_cross = Counter(x for i in idx for x in cross[i])
        seg_own = Counter(x for c in members for x in (c.get("purchase_categories") or []))

        def lift(counter, overall):
            rows = []
            for key, cnt in counter.most_common():
                share = cnt / m
                base = overall[key] / n
                rows.append({"label": key, "share": round(100 * share), "lift": round(share / base, 2) if base else 0})
            return sorted(rows, key=lambda r: (-r["share"] * r["lift"]))[:6]

        value = sum(c["lifetime_value"] or 0 for c in members)
        segments.append({
            "id": j,
            "size": m,
            "size_pct": round(100 * m / n),
            "value": round(value),
            "value_pct": round(100 * value / total_value),
            "avg_ltv": round(value / m),
            "avg_engagement": round(sum(c["engagement_score"] or 0 for c in members) / m, 1),
            "avg_purchases": round(sum(c.get("purchase_count") or 0 for c in members) / m, 1),
            "avg_recency_days": round(sum(_recency_days(c, today) for c in members) / m),
            "at_risk_pct": round(100 * sum(c["phase"] in AT_RISK for c in members) / m),
            "loyal_pct": round(100 * sum(c["phase"] in LOYAL for c in members) / m),
            "interests": lift(seg_interest, overall_interest),
            "cross_industry": lift(seg_cross, overall_cross),
            "own_categories": [{"label": k2, "share": round(100 * v / m)} for k2, v in seg_own.most_common(5)],
            "countries": [k2 for k2, _ in Counter(c["country"] for c in members if c["country"]).most_common(4)],
            "phases": dict(Counter(c["phase"] for c in members)),
            "prior_labels": dict(Counter(c["archetype"] for c in members if c["archetype"])),
            "signals": [c["behavioral_signals"] for c in members if c.get("behavioral_signals")][:6],
        })
    return {
        "assignments": {str(clients[i]["id"]): int(labels[i]) for i in range(n)},
        "segments": segments,
        "quality": {"clients": n, "k": kk, "silhouette": round(sil, 3),
                    "features": {"interest_clusters": len(interests), "cross_industry": len(cross_vocab),
                                 "own_categories": len(own)},
                    "data_coverage": {
                        "interests": round(100 * sum(bool(c["interests"]) for c in clients) / n),
                        "cross_purchases": round(100 * sum(bool(r) for r in cross) / n),
                        "purchase_history": round(100 * sum(bool(c.get("purchase_count")) for c in clients) / n),
                        "last_purchase": round(100 * sum(bool(parse_date(c.get("last_purchase"))) for c in clients) / n),
                    }},
    }
