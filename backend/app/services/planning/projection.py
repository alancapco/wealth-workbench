"""Deterministic retirement math. The model may narrate these figures; it does not compute them."""
from __future__ import annotations

from datetime import date


def _compound(
    *,
    years: int,
    current_savings: float,
    monthly_contribution: float,
    annual_return_pct: float,
    inflation_pct: float,
    current_age: int,
    target: float,
) -> dict:
    r = annual_return_pct / 100.0
    i = inflation_pct / 100.0
    monthly_r = r / 12.0
    months = max(years, 0) * 12
    fv_lump = current_savings * ((1 + r) ** years)
    if monthly_r > 0 and months:
        fv_annuity = (monthly_contribution / 1_000_000) * (((1 + monthly_r) ** months - 1) / monthly_r)
    else:
        fv_annuity = (monthly_contribution / 1_000_000) * months
    projected = round(fv_lump + fv_annuity, 4)
    inflation_factor = (1 + i) ** years if i > -1 else 1.0
    adjusted_target = round(target * inflation_factor, 4)
    real_projected = round(projected / inflation_factor, 4) if inflation_factor else projected
    gap = round(adjusted_target - projected, 4)
    real_gap = round(real_projected - target, 4)
    probability = (
        min(100.0, max(0.0, round(100.0 * projected / adjusted_target, 1)))
        if adjusted_target > 0
        else 100.0
    )
    step = max(1, years // 5) if years else 1
    milestones = []
    for yr in range(0, years + 1, step):
        fv_l = current_savings * ((1 + r) ** yr)
        m = yr * 12
        if monthly_r > 0 and m:
            fv_a = (monthly_contribution / 1_000_000) * (((1 + monthly_r) ** m - 1) / monthly_r)
        else:
            fv_a = (monthly_contribution / 1_000_000) * m
        yr_factor = (1 + i) ** yr if i > -1 else 1.0
        nominal = round(fv_l + fv_a, 4)
        milestones.append({
            "year": date.today().year + yr,
            "age": current_age + yr,
            "corpus_usd_millions": nominal,
            "real_corpus_usd_millions": round(nominal / yr_factor, 4) if yr_factor else nominal,
            "inflation_adjusted_target_usd_millions": round(target * yr_factor, 4),
        })
    return {
        "projected_corpus_usd_millions": round(projected, 2),
        "probability_of_success_pct": probability,
        "year_by_year": milestones,
        "inflation_adjusted_target_usd_millions": round(adjusted_target, 2),
        "real_projected_corpus_usd_millions": round(real_projected, 2),
        "real_terms_gap_usd_millions": round(real_gap, 2),
        "gap_usd_millions": round(gap, 2),
        "real_return_pct": round(((1 + r) / (1 + i) - 1) * 100, 2) if i > -1 else round(r * 100, 2),
    }


def project_plan(
    *,
    current_age: int,
    retirement_age: int,
    current_savings_usd_millions: float,
    monthly_contribution_usd: float,
    target_retirement_corpus_usd_millions: float,
    assumed_annual_return_pct: float = 6.0,
    inflation_pct: float = 2.5,
) -> dict:
    """Nominal and real corpus, plus conservative and upside bands. No model calls."""
    years = max(retirement_age - current_age, 0)
    target = target_retirement_corpus_usd_millions
    base = _compound(
        years=years,
        current_savings=current_savings_usd_millions,
        monthly_contribution=monthly_contribution_usd,
        annual_return_pct=assumed_annual_return_pct,
        inflation_pct=inflation_pct,
        current_age=current_age,
        target=target,
    )
    conservative = _compound(
        years=years,
        current_savings=current_savings_usd_millions,
        monthly_contribution=monthly_contribution_usd,
        annual_return_pct=max(assumed_annual_return_pct - 2, 0),
        inflation_pct=inflation_pct,
        current_age=current_age,
        target=target,
    )
    upside = _compound(
        years=years,
        current_savings=current_savings_usd_millions,
        monthly_contribution=monthly_contribution_usd,
        annual_return_pct=assumed_annual_return_pct + 2,
        inflation_pct=inflation_pct,
        current_age=current_age,
        target=target,
    )
    gap = base["gap_usd_millions"]
    months = max(years * 12, 1)
    if gap > 0:
        extra = round(gap * 1_000_000 / months, 0)
        recommendations = [
            f"Increase monthly contributions by about USD {extra:,.0f} to close the inflation-adjusted gap.",
            "Keep the growth sleeve inside the client's risk band; do not fund the gap with a higher-risk product.",
        ]
        gap_analysis = (
            f"Gap of USD {abs(gap)}M below the inflation-adjusted target of "
            f"USD {base['inflation_adjusted_target_usd_millions']}M "
            f"(USD {abs(base['real_terms_gap_usd_millions'])}M in today's dollars)."
        )
    else:
        recommendations = [
            "The illustrated path meets the inflation-adjusted target.",
            "Review the income sleeve as the retirement date approaches.",
        ]
        gap_analysis = (
            f"Surplus of USD {abs(gap)}M above the inflation-adjusted target of "
            f"USD {base['inflation_adjusted_target_usd_millions']}M."
        )
    summary = (
        f"Deterministic projection at {assumed_annual_return_pct}% a year with {inflation_pct}% inflation: "
        f"nominal corpus USD {base['projected_corpus_usd_millions']}M at age {retirement_age} "
        f"(USD {base['real_projected_corpus_usd_millions']}M in today's dollars)."
    )
    return {
        "summary": summary,
        "projected_corpus_usd_millions": base["projected_corpus_usd_millions"],
        "probability_of_success_pct": base["probability_of_success_pct"],
        "year_by_year": base["year_by_year"],
        "gap_analysis": gap_analysis,
        "recommendations": recommendations,
        "inflation_pct": inflation_pct,
        "inflation_adjusted_target_usd_millions": base["inflation_adjusted_target_usd_millions"],
        "real_return_pct": base["real_return_pct"],
        "real_projected_corpus_usd_millions": base["real_projected_corpus_usd_millions"],
        "real_terms_gap_usd_millions": base["real_terms_gap_usd_millions"],
        "gap_usd_millions": gap,
        "scenarios": {
            "conservative": {
                "return_pct": max(assumed_annual_return_pct - 2, 0),
                "projected_corpus_usd_millions": conservative["projected_corpus_usd_millions"],
                "year_by_year": conservative["year_by_year"],
            },
            "base": {
                "return_pct": assumed_annual_return_pct,
                "projected_corpus_usd_millions": base["projected_corpus_usd_millions"],
                "year_by_year": base["year_by_year"],
            },
            "upside": {
                "return_pct": assumed_annual_return_pct + 2,
                "projected_corpus_usd_millions": upside["projected_corpus_usd_millions"],
                "year_by_year": upside["year_by_year"],
            },
        },
        "engine": "deterministic",
    }
