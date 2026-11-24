"""AI showcase contracts that do not need Postgres or a live model."""
import pytest

from app.services.graph.neo4j_service import assemble_graph
from app.services.journey.briefing import build_brief
from app.services.journey.logic import extract_profile_updates
from app.services.journey.meeting_ai import _ground, sample_for
from app.services.planning.projection import project_plan


def test_projection_keeps_inflation_math_deterministic():
    report = project_plan(
        current_age=50,
        retirement_age=60,
        current_savings_usd_millions=1,
        monthly_contribution_usd=0,
        target_retirement_corpus_usd_millions=2,
        assumed_annual_return_pct=0,
        inflation_pct=0,
    )
    assert report["projected_corpus_usd_millions"] == 1
    assert report["gap_usd_millions"] == 1
    assert report["scenarios"]["upside"]["projected_corpus_usd_millions"] > 1
    assert report["engine"] == "deterministic"


def test_meeting_extractor_quotes_the_transcript():
    text = "Please treat the risk profile as balanced and the investment objective is income."
    proposals = extract_profile_updates(text)
    grounded = _ground(proposals, text)
    fields = {item["field"] for item in grounded}
    assert "risk_profile" in fields
    assert "investment_objective" in fields
    assert _ground([{"field": "goal", "value": "Yacht", "evidence": "a yacht"}], text) == []


def test_samples_match_the_two_demo_personas():
    assert sample_for("Tan Wei Liang")["persona"] == "tan"
    assert "Shariah" in sample_for("Ahmad Rahman")["transcript"] or "screened" in sample_for("Ahmad Rahman")["transcript"]


def test_tan_graph_includes_the_trust_and_a_rule():
    graph = assemble_graph(
        {
            "id": "tan-1",
            "name": "Tan Family Office",
            "family_office_name": "Tan Family Office",
            "country": "Singapore",
            "shariah_compliant": False,
        },
        [{"asset_name": "SGD bond", "allocation_pct": 10}],
    )
    kinds = {node["kind"] for node in graph["nodes"]}
    assert "Trust" in kinds
    assert "WealthRule" in kinds
    assert graph["source"] == "postgres_fallback"
    assert graph["lookthrough_summary"]["trusts"] >= 1
    plain = assemble_graph(
        {
            "id": "tan-person",
            "name": "Yuki Tanaka",
            "family_office_name": None,
            "country": "Singapore",
            "shariah_compliant": False,
        },
        [],
    )
    assert "Trust" not in {node["kind"] for node in plain["nodes"]}


def test_shariah_client_is_linked_to_aaoifi():
    graph = assemble_graph(
        {
            "id": "ahmad-1",
            "name": "Ahmad Rahman",
            "family_office_name": None,
            "country": "Singapore",
            "shariah_compliant": True,
        },
        [],
    )
    names = [node["name"] for node in graph["nodes"]]
    assert any("AAOIFI" in name for name in names)


@pytest.mark.asyncio
async def test_brief_uses_the_deterministic_sections_when_the_model_is_absent(monkeypatch):
    async def _silent(*_args, **_kwargs):
        return None

    monkeypatch.setattr("app.services.journey.briefing.complete_json", _silent)
    brief = await build_brief({
        "client_id": "c1",
        "name": "Ahmad Rahman",
        "profile": {"jurisdiction": "SG", "shariah_compliant": True, "aum_usd_millions": 12},
        "investor": {"rpq_band": "Moderate", "expiry_date": "2027-01-01", "vulnerable": False},
        "financial_profile": {"investment_objective": "Growth"},
        "holdings": [{"asset_name": "Sukuk", "allocation_pct": 40}],
        "saa": [],
        "opportunities": [],
    })
    assert brief["ai"]["source"] == "deterministic"
    assert set(brief["sections"]) == {
        "portfolio_overview",
        "material_changes",
        "recent_interactions",
        "market_news",
        "proposed_agenda",
    }
    assert "Ahmad Rahman" in brief["sections"]["portfolio_overview"]["narrative"]
