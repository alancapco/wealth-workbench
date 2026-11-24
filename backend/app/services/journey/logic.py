"""Pure journey rules. No database. Used by the API and by tests.

Thresholds live in JOURNEY_POLICY so they are configuration, not scattered
literals. The pack is labelled DEMO until Compliance and Sales sign DEP-02/05.
"""
from __future__ import annotations

from datetime import date, timedelta

JOURNEY_POLICY = {
    "source": "DEMO_RULE_SET_NOT_APPROVED",
    "auto_approval_limit_usd": 500_000,
    "discount_threshold_pct": 0.5,
    "rpq_window_days": 30,
    "maturity_window_days": 90,
    "drift_threshold_pct": 8.0,
    "saa": {
        "Conservative": {"Fixed Income": 55, "Equities": 20, "Cash": 15, "Alternatives": 10},
        "Moderate": {"Fixed Income": 35, "Equities": 40, "Cash": 10, "Alternatives": 15},
        "Balanced": {"Fixed Income": 30, "Equities": 45, "Cash": 10, "Alternatives": 15},
        "Aggressive": {"Fixed Income": 15, "Equities": 60, "Cash": 5, "Alternatives": 20},
    },
}

PIPELINE_STAGES = [
    "ACTIONABLE",
    "CONTACTED_ENGAGED",
    "DISCOVERY_RECOMMENDATION",
    "CLIENT_ACCEPTANCE",
    "TRADE_EXECUTION",
    "SALES_REALIZED",
]

# Mandatory financial-profile fields (DEC-FP-01 default until Product confirms).
FINANCIAL_PROFILE_FIELDS = (
    "annual_income_band",
    "investable_assets_band",
    "liquidity_need",
    "investment_objective",
)

CATALOGUE = [
    {
        "product_id": "BOND-HSBC-2029",
        "name": "HSBC 4.2% 2029 Senior Bond",
        "order_type": "BOND",
        "cio_rating": "OVERWEIGHT",
        "rationale": "CIO prefers high-grade SGD/USD credit for conservative and moderate books.",
        "share_class": "ACC",
        "saa_bucket": "Fixed Income",
        "complexity": "PLAIN",
        "jurisdictions": ["SG", "HK"],
        "risk_band": "Conservative",
        "min_usd": 50_000,
        "shariah": False,
    },
    {
        "product_id": "UT-GLOBAL-EQ",
        "name": "Global Equity Unit Trust A",
        "order_type": "UT",
        "cio_rating": "NEUTRAL",
        "rationale": "Core equity sleeve aligned to moderate and balanced SAA.",
        "share_class": "A",
        "saa_bucket": "Equities",
        "complexity": "PLAIN",
        "jurisdictions": ["SG", "HK"],
        "risk_band": "Moderate",
        "min_usd": 10_000,
        "shariah": False,
    },
    {
        "product_id": "SN-EQ-LINKED",
        "name": "Equity-linked Structured Note",
        "order_type": "SN",
        "cio_rating": "UNDERWEIGHT",
        "rationale": "Only where CKA is current and the client is not vulnerable.",
        "share_class": "N/A",
        "saa_bucket": "Alternatives",
        "complexity": "COMPLEX",
        "jurisdictions": ["SG", "HK"],
        "risk_band": "Aggressive",
        "min_usd": 100_000,
        "shariah": False,
    },
    {
        "product_id": "DCI-USD-SGD",
        "name": "USD/SGD Dual Currency Investment",
        "order_type": "DCI",
        "cio_rating": "NEUTRAL",
        "rationale": "Cash-plus for clients who accept currency conversion risk.",
        "share_class": "N/A",
        "saa_bucket": "Cash",
        "complexity": "COMPLEX",
        "jurisdictions": ["SG"],
        "risk_band": "Moderate",
        "min_usd": 25_000,
        "shariah": False,
    },
    {
        "product_id": "UT-SUKUK",
        "name": "Global Sukuk Fund",
        "order_type": "UT",
        "cio_rating": "OVERWEIGHT",
        "rationale": "Shariah sleeve for clients with a compliance preference.",
        "share_class": "I",
        "saa_bucket": "Fixed Income",
        "complexity": "PLAIN",
        "jurisdictions": ["SG", "HK"],
        "risk_band": "Conservative",
        "min_usd": 10_000,
        "shariah": True,
    },
]


def jurisdiction_code(country: str | None) -> str:
    text = (country or "").upper()
    if "HONG" in text or text == "HK":
        return "HK"
    if "SING" in text or text == "SG":
        return "SG"
    return "SG"


def days_until(expiry: date | None, today: date | None = None) -> int | None:
    if expiry is None:
        return None
    return (expiry - (today or date.today())).days


def score_lead(signals: list[dict], control: str | None = None) -> dict:
    """Weighted propensity. Pin lifts, snooze and dismiss drop the lead."""
    if control == "DISMISS":
        return {"score": 0, "rankable": False, "reasons": ["Dismissed by the RM"]}
    if control == "SNOOZE":
        return {"score": 0, "rankable": False, "reasons": ["Snoozed by the RM"]}
    weights = {
        "RPQ_EXPIRY": 30,
        "MARKET_MOVE": 20,
        "SAA_DRIFT": 25,
        "MATURITY": 15,
        "INACTIVITY": 10,
        "OPPORTUNITY": 15,
    }
    score = 0
    reasons = []
    for signal in signals:
        kind = signal.get("kind")
        weight = weights.get(kind, 5)
        score += weight
        reasons.append(signal.get("summary") or kind)
    if control == "PIN":
        score += 1000
        reasons.insert(0, "Pinned by the RM")
    return {"score": score, "rankable": True, "reasons": reasons or ["No active signal"]}


def drift_vs_saa(allocation: dict[str, float], risk_profile: str | None) -> list[dict]:
    target = JOURNEY_POLICY["saa"].get(risk_profile or "Moderate", JOURNEY_POLICY["saa"]["Moderate"])
    rows = []
    for bucket, target_pct in target.items():
        actual = float(allocation.get(bucket, 0))
        gap = round(actual - target_pct, 2)
        rows.append({
            "bucket": bucket,
            "target_pct": target_pct,
            "actual_pct": round(actual, 2),
            "drift_pct": gap,
            "breach": abs(gap) >= JOURNEY_POLICY["drift_threshold_pct"],
        })
    return rows


def assess_product(profile: dict, product: dict) -> dict:
    """SG and HK suitability for the journey shortlist.

    HARD MISSING or HARD FAIL is never ticket-eligible. A missing SG pack must
    not fall through to HK rules (B-13).
    """
    jurisdiction = profile.get("jurisdiction") or "SG"
    factors = []

    def add(key, classification, result, explanation):
        factors.append({
            "key": key,
            "classification": classification,
            "result": result,
            "explanation": explanation,
        })

    if profile.get("rpq_expired") or profile.get("rpq_band") in (None, ""):
        add("profile_validity", "HARD", "FAIL" if profile.get("rpq_expired") else "MISSING",
            "Investor profile is expired or missing. Cannot be GREEN.")
    else:
        add("profile_validity", "HARD", "PASS", f"RPQ band {profile.get('rpq_band')} is current.")

    product_markets = product.get("jurisdictions") or []
    if jurisdiction not in product_markets:
        add("cross_border", "HARD", "FAIL",
            f"Product is not eligible in {jurisdiction}. HK rules are not applied to an SG client, and the reverse.")
    elif profile.get("cross_border_restricted"):
        add("cross_border", "HARD", "FAIL", "Booking centre and residence do not match the product domicile.")
    else:
        add("cross_border", "HARD", "PASS", f"Eligible in {jurisdiction}.")

    risk_order = ["Conservative", "Moderate", "Balanced", "Aggressive"]
    client_risk = profile.get("risk_profile") or "Moderate"
    product_risk = product.get("risk_band") or "Moderate"
    if client_risk in risk_order and product_risk in risk_order:
        if risk_order.index(product_risk) > risk_order.index(client_risk) + 1:
            add("risk_match", "HARD", "FAIL", "Product risk is above the client's band.")
        else:
            add("risk_match", "HARD", "PASS", "Product risk is within the client's band.")
    else:
        add("risk_match", "HARD", "MISSING", "Risk band is missing.")

    if product.get("complexity") == "COMPLEX" and not profile.get("cka_passed"):
        add("cka", "HARD", "FAIL", "Complex product requires a current CKA.")
    else:
        add("cka", "HARD", "PASS", "CKA is current, or the product is not complex.")

    if profile.get("vulnerable"):
        add("vulnerable_client", "HARD", "WARN", "Vulnerable client. Checker required; not auto-approved.")
    else:
        add("vulnerable_client", "SOFT", "PASS", "Not flagged vulnerable.")

    if profile.get("high_risk_segment"):
        add("high_risk_segment", "HARD", "WARN", "High-risk segment. Checker required.")
    else:
        add("high_risk_segment", "SOFT", "PASS", "Not a high-risk segment.")

    if profile.get("shariah_compliant") and not product.get("shariah"):
        add("preference", "HARD", "FAIL", "Client requires a Shariah-compliant product.")
    else:
        add("preference", "SOFT", "PASS", "Product matches recorded preferences.")

    hard_fail = any(f["classification"] == "HARD" and f["result"] == "FAIL" for f in factors)
    hard_block = any(f["classification"] == "HARD" and f["result"] in ("FAIL", "MISSING") for f in factors)
    any_warn = any(f["result"] in ("FAIL", "WARN", "MISSING") for f in factors)
    if hard_fail:
        rating = "RED"
    elif hard_block or any_warn:
        rating = "YELLOW"
    else:
        rating = "GREEN"
    # HARD MISSING is not ticket-eligible (B-14). WARN still needs a checker at Act.
    ticket_eligible = (rating == "GREEN" or rating == "YELLOW") and not hard_block
    return {
        "rating": rating,
        "ticket_eligible": ticket_eligible,
        "factors": factors,
        "jurisdiction": jurisdiction,
        "rule_pack": f"{jurisdiction}_DEMO",
        "rule_source": JOURNEY_POLICY["source"],
    }


def auto_approval(profile: dict, items: list[dict], signed: bool, rating: str) -> dict:
    """Maker is not required to be checker only when every gate below passes."""
    reasons = []
    if not signed:
        reasons.append("Client has not signed the cart")
    if rating != "GREEN":
        reasons.append(f"Suitability is {rating}, not GREEN")
    if profile.get("vulnerable"):
        reasons.append("Vulnerable client")
    if profile.get("high_risk_segment"):
        reasons.append("High-risk segment")
    if profile.get("cross_border_restricted"):
        reasons.append("Cross-border restriction")
    notional = sum(float(i.get("amount_usd") or 0) for i in items)
    if notional > JOURNEY_POLICY["auto_approval_limit_usd"]:
        reasons.append("Notional is above the auto-approval limit")
    if any((i.get("discount_pct") or 0) > JOURNEY_POLICY["discount_threshold_pct"] for i in items):
        reasons.append("Discount is above the sales-manager threshold")
    if any(i.get("complexity") == "COMPLEX" and not profile.get("cka_passed") for i in items):
        reasons.append("Complex product without CKA")
    return {
        "eligible": not reasons,
        "reasons": reasons or ["Eligible for auto-approval"],
        "notional_usd": notional,
        "limit_usd": JOURNEY_POLICY["auto_approval_limit_usd"],
        "policy_source": JOURNEY_POLICY["source"],
    }


def catalogue_search(query: str) -> list[dict]:
    q = (query or "").lower()
    return [
        product for product in CATALOGUE
        if not q or q in product["name"].lower() or q in product["order_type"].lower() or q in product["saa_bucket"].lower()
    ]


def optimise(allocation: dict[str, float], risk_profile: str | None, shariah: bool) -> list[dict]:
    """One-click proposal: suggest catalogue products for buckets that are under SAA."""
    gaps = [row for row in drift_vs_saa(allocation, risk_profile) if row["drift_pct"] < 0]
    proposals = []
    for gap in gaps:
        candidates = [p for p in CATALOGUE if p["saa_bucket"] == gap["bucket"]]
        if shariah:
            compliant = [p for p in candidates if p["shariah"]]
            candidates = compliant or candidates
        if not candidates:
            continue
        product = candidates[0]
        proposals.append({
            "product_id": product["product_id"],
            "name": product["name"],
            "order_type": product["order_type"],
            "bucket": gap["bucket"],
            "drift_pct": gap["drift_pct"],
            "illustrative": True,
            "note": "Proposal only. Does not submit to OMS.",
        })
    return proposals


def pitch(profile: dict, product: dict, assessment: dict) -> dict:
    if assessment["rating"] == "RED":
        return {
            "allowed": False,
            "text": "No pitch. Suitability is RED, so the product is not explained as a recommendation.",
            "evidence": [f["key"] for f in assessment["factors"] if f["result"] == "FAIL"],
        }
    text = (
        f"{product['name']} is on the CIO {product['cio_rating'].lower()} list because {product['rationale']} "
        f"It sits in the {product['saa_bucket']} sleeve (share class {product['share_class']}). "
        f"For this client the suitability pre-screen is {assessment['rating']} under the {assessment['rule_pack']} pack. "
        "This is a pre-screen, not compliance approval."
    )
    return {"allowed": True, "text": text, "evidence": [product["product_id"], assessment["rule_pack"]]}


def protect_answer(question: str) -> dict:
    """Citation-required policy Q&A. No citation means no answer."""
    q = (question or "").lower()
    library = [
        {
            "keywords": ("cross-border", "booking", "residence"),
            "citation": "SG-XB-01",
            "text": "A product may be discussed only when the booking centre, the client's residence and the product domicile are all in the eligible set. Otherwise the cross-border factor is a hard fail.",
        },
        {
            "keywords": ("vulnerable",),
            "citation": "SG-VC-02",
            "text": "A vulnerable client always requires a sales-manager checker. Auto-approval must not fire.",
        },
        {
            "keywords": ("cka", "complex", "structured"),
            "citation": "MAS-CKA-03",
            "text": "Complex products require a current Customer Knowledge Assessment. A missing CKA is a hard fail.",
        },
        {
            "keywords": ("rpq", "expir", "investor profile"),
            "citation": "SG-RPQ-04",
            "text": "An expired or missing RPQ cannot produce a GREEN suitability result, and blocks cart hand-off.",
        },
    ]
    hits = [row for row in library if any(word in q for word in row["keywords"])]
    if not hits:
        return {"answered": False, "text": "Insufficient evidence. No policy clause matched this question.", "citations": []}
    return {
        "answered": True,
        "text": " ".join(row["text"] for row in hits),
        "citations": [row["citation"] for row in hits],
    }


def extract_profile_updates(transcript: str) -> list[dict]:
    """Deterministic assist. Proposals only — nothing is applied until accepted."""
    text = transcript or ""
    lower = text.lower()
    proposals = []
    # Evidence is a verbatim fragment so a later check can confirm it sits in the transcript.
    if "conservative" in lower:
        proposals.append({"field": "risk_profile", "value": "Conservative", "evidence": "conservative"})
    if "balanced" in lower:
        proposals.append({"field": "risk_profile", "value": "Balanced", "evidence": "balanced"})
    elif "moderate" in lower:
        proposals.append({"field": "risk_profile", "value": "Moderate", "evidence": "moderate"})
    if "retirement" in lower or "retire" in lower:
        proposals.append({"field": "goal", "value": "Retirement", "evidence": "retirement" if "retirement" in lower else "retire"})
    if "philanthropy" in lower:
        proposals.append({"field": "goal", "value": "Philanthropy", "evidence": "philanthropy"})
    if "education" in lower:
        proposals.append({"field": "goal", "value": "Education", "evidence": "education"})
    if "income" in lower:
        proposals.append({"field": "investment_objective", "value": "Income", "evidence": "income"})
    if "growth" in lower:
        proposals.append({"field": "investment_objective", "value": "Growth", "evidence": "growth"})
    return proposals


def stress(total_usd: float, shocks: dict) -> dict:
    market = float(shocks.get("market_shock_pct") or 0) / 100
    fx = float(shocks.get("fx_shock_pct") or 0) / 100
    sector = float(shocks.get("sector_shock_pct") or 0) / 100
    impact = total_usd * (market + fx * 0.4 + sector * 0.2)
    return {
        "total_usd": total_usd,
        "impact_usd": round(impact, 2),
        "stressed_usd": round(total_usd + impact, 2),
        "assumptions": {"market": market, "fx_weight": 0.4, "sector_weight": 0.2, "illustrative": True},
    }


def next_stage(stage: str) -> str | None:
    if stage not in PIPELINE_STAGES:
        return None
    index = PIPELINE_STAGES.index(stage)
    if index + 1 >= len(PIPELINE_STAGES):
        return None
    return PIPELINE_STAGES[index + 1]


def default_expiry(today: date | None = None, days: int = 20) -> date:
    return (today or date.today()) + timedelta(days=days)
