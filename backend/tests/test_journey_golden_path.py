"""Golden path for Engage → Discover → Recommend → Act → Service.

These tests exercise the journey rules without a database. The HTTP routes
are covered when Postgres is available; the rules are the contract.
"""
from datetime import date, timedelta

from app.services.journey.logic import (
    PIPELINE_STAGES,
    assess_product,
    auto_approval,
    drift_vs_saa,
    extract_profile_updates,
    next_stage,
    optimise,
    pitch,
    protect_answer,
    score_lead,
    stress,
)
from app.services.product.rule_sets import rule_set_for


def _profile(**overrides):
    base = {
        "jurisdiction": "SG",
        "risk_profile": "Moderate",
        "rpq_band": "Moderate",
        "rpq_expired": False,
        "cka_passed": True,
        "vulnerable": False,
        "high_risk_segment": False,
        "cross_border_restricted": False,
        "shariah_compliant": False,
        "investor_status": "ACCREDITED",
    }
    base.update(overrides)
    return base


def test_engage_scoring_applies_pin_and_drops_snooze():
    signals = [{"kind": "RPQ_EXPIRY", "summary": "RPQ inside 30 days"}]
    ranked = score_lead(signals)
    pinned = score_lead(signals, "PIN")
    snoozed = score_lead(signals, "SNOOZE")
    assert ranked["rankable"] is True
    assert pinned["score"] > ranked["score"]
    assert snoozed["rankable"] is False


def test_discover_assist_proposes_and_does_not_invent():
    proposals = extract_profile_updates("The client wants moderate growth for retirement.")
    fields = {item["field"] for item in proposals}
    assert "risk_profile" in fields
    assert "goal" in fields
    assert extract_profile_updates("hello") == []


def test_recommend_sg_pack_does_not_use_hk_for_ineligible_product():
    assert rule_set_for("SG") is not None
    assert rule_set_for("HK") is not None
    assert rule_set_for("SG") is not rule_set_for("HK")
    dci = {
        "name": "DCI",
        "jurisdictions": ["SG"],
        "risk_band": "Moderate",
        "complexity": "COMPLEX",
        "shariah": False,
        "cio_rating": "NEUTRAL",
        "rationale": "cash plus",
        "share_class": "N/A",
        "saa_bucket": "Cash",
        "product_id": "DCI-USD-SGD",
    }
    hk_client = assess_product(_profile(jurisdiction="HK"), dci)
    assert hk_client["rating"] == "RED"
    assert hk_client["ticket_eligible"] is False
    assert hk_client["rule_pack"].startswith("HK")
    missing = assess_product(_profile(rpq_band=None, rpq_expired=False), dci)
    assert missing["ticket_eligible"] is False


def test_recommend_pitch_blocked_on_red_and_protect_requires_citation():
    product = {
        "name": "Note",
        "cio_rating": "UNDERWEIGHT",
        "rationale": "only with CKA",
        "share_class": "N/A",
        "saa_bucket": "Alternatives",
        "product_id": "SN",
    }
    red = {"rating": "RED", "rule_pack": "SG_DEMO", "factors": [{"key": "cka", "result": "FAIL"}]}
    assert pitch(_profile(), product, red)["allowed"] is False
    refused = protect_answer("what is the weather")
    assert refused["answered"] is False
    assert refused["citations"] == []
    cited = protect_answer("Is a vulnerable client allowed to auto-approve a complex product?")
    assert cited["answered"] is True
    assert cited["citations"]


def test_act_green_bond_auto_approves_and_vulnerable_does_not():
    items = [{"amount_usd": 100000, "discount_pct": 0, "complexity": "PLAIN"}]
    green = auto_approval(_profile(), items, signed=True, rating="GREEN")
    assert green["eligible"] is True
    unsigned = auto_approval(_profile(), items, signed=False, rating="GREEN")
    assert unsigned["eligible"] is False
    vulnerable = auto_approval(_profile(vulnerable=True), items, signed=True, rating="GREEN")
    assert vulnerable["eligible"] is False
    assert any("Vulnerable" in reason for reason in vulnerable["reasons"])


def test_act_pipeline_advances_to_sales_realized():
    stage = "ACTIONABLE"
    seen = [stage]
    while True:
        nxt = next_stage(stage)
        if nxt is None:
            break
        stage = nxt
        seen.append(stage)
    assert seen == PIPELINE_STAGES
    assert stage == "SALES_REALIZED"


def test_service_drift_and_projection_are_labelled():
    rows = drift_vs_saa({"Equities": 80, "Fixed Income": 10, "Cash": 5, "Alternatives": 5}, "Conservative")
    assert any(row["breach"] for row in rows)
    proposal = optimise({"Equities": 80, "Cash": 20}, "Conservative", shariah=False)
    assert proposal
    assert all(item["illustrative"] for item in proposal)
    shocked = stress(1_000_000, {"market_shock_pct": -10, "fx_shock_pct": 0, "sector_shock_pct": 0})
    assert shocked["stressed_usd"] < shocked["total_usd"]
    assert shocked["assumptions"]["illustrative"] is True


def test_rpq_window_constant_is_thirty_days():
    from app.services.journey.logic import JOURNEY_POLICY
    assert JOURNEY_POLICY["rpq_window_days"] == 30
    assert date.today() + timedelta(days=30)
