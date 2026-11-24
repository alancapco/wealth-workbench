"""Jurisdiction-driven suitability rule sets.

The assessment service asks this registry for the factors that apply to a client's
jurisdiction. Thresholds, disclosure lists and risk scales come from the approved
policy configuration; an absent input yields MISSING/FAIL rather than a PASS.
"""
from typing import Callable

from app.schemas.common import Money
from app.schemas.product import SuitabilityFactor


def _factor(
    key: str,
    label: str,
    classification: str,
    result: str,
    explanation: str,
    override_permitted: bool = False,
) -> SuitabilityFactor:
    return SuitabilityFactor(
        key=key,
        label=label,
        classification=classification,  # type: ignore[arg-type]
        result=result,  # type: ignore[arg-type]
        evidence_refs=[],
        explanation=explanation,
        override_permitted=override_permitted,
    )


def _risk_rank(scale: dict, value: str | None) -> int | None:
    if not value or not isinstance(scale, dict):
        return None
    rank = scale.get(str(value).strip().upper())
    return rank if isinstance(rank, int) else None


def evaluate_hk(
    policy: dict,
    profile: dict,
    product: dict,
    amount: Money | None,
    account_ref: str | None,
) -> list[SuitabilityFactor]:
    """HK SFC suitability: reasonable basis, risk match, complexity, disclosure.

    Plus the generic objective/concentration factors. Hard factors are not
    overridable; soft factors can be overridden with a recorded rationale.
    """
    factors: list[SuitabilityFactor] = []

    objectives = product.get("investment_objectives") or []
    horizon = profile.get("investment_horizon_years")
    liquidity = profile.get("liquidity_needs")
    product_horizon = product.get("minimum_investment_years")
    if not objectives or not horizon or not liquidity:
        reasonable = "MISSING"
        basis_reason = (
            "Reasonable basis cannot be established: product objectives, client "
            "investment horizon or liquidity needs are absent."
        )
    elif product_horizon is not None and int(product_horizon) > int(horizon):
        reasonable = "FAIL"
        basis_reason = (
            f"Product minimum horizon {product_horizon}y exceeds client horizon {horizon}y."
        )
    else:
        reasonable = "PASS"
        basis_reason = (
            f"Product objectives {objectives} are supported by client horizon "
            f"{horizon}y and liquidity needs {liquidity}."
        )
    factors.append(_factor(
        "hk_reasonable_basis", "Reasonable Basis for Recommendation", "HARD",
        reasonable, basis_reason,
    ))

    scale = policy.get("risk_scale")
    client_rank = _risk_rank(scale, profile.get("risk_tolerance"))
    product_rank = _risk_rank(scale, product.get("risk_code"))
    if client_rank is None or product_rank is None:
        risk_result = "MISSING"
        risk_reason = (
            "Risk match cannot be established: client tolerance or product risk "
            "code is missing from the approved risk scale."
        )
    elif product_rank > client_rank:
        risk_result = "FAIL"
        risk_reason = (
            f"Product risk rank {product_rank} exceeds client tolerance rank {client_rank}."
        )
    else:
        risk_result = "PASS"
        risk_reason = f"Product risk rank {product_rank} is within client tolerance rank {client_rank}."
    factors.append(_factor("risk_match", "Risk Tolerance Match", "HARD", risk_result, risk_reason))

    complex_levels = [str(v).upper() for v in (policy.get("complexity_levels") or [])]
    complexity = str(product.get("complexity") or "").upper()
    if not complex_levels:
        complexity_result = "MISSING"
        complexity_reason = "Approved policy does not declare which product complexity levels require assessment."
    elif complexity in complex_levels:
        experience = profile.get("complexity_acknowledged")
        complexity_result = "PASS" if experience else "MISSING"
        complexity_reason = (
            "Client understanding of the complex product is evidenced in the KYC record."
            if experience else
            f"Product is {complexity}; no client complexity acknowledgement or investment experience on record."
        )
    else:
        complexity_result = "PASS"
        complexity_reason = f"Product complexity '{complexity or 'VANILLA'}' is not in the policy complex-product list."
    factors.append(_factor(
        "complexity_assessment", "Product Complexity Assessment", "HARD",
        complexity_result, complexity_reason,
    ))

    required_disclosures = policy.get("required_disclosures") or []
    if not required_disclosures:
        disclosure_result = "MISSING"
        disclosure_reason = "Approved policy does not declare the required HK disclosure obligations."
    else:
        missing = [d for d in required_disclosures if not product.get(d)]
        disclosure_result = "MISSING" if missing else "PASS"
        disclosure_reason = (
            f"Missing disclosure evidence: {', '.join(missing)}."
            if missing else
            f"All required disclosures present: {', '.join(required_disclosures)}."
        )
    factors.append(_factor(
        "disclosure_obligations", "Disclosure Obligations", "HARD",
        disclosure_result, disclosure_reason,
    ))

    client_objectives = profile.get("investment_objectives") or []
    if not client_objectives or not objectives:
        objective_result = "MISSING"
        objective_reason = "Client or product investment objectives are not recorded."
    elif set(map(str, client_objectives)).isdisjoint(map(str, objectives)):
        objective_result = "WARN"
        objective_reason = f"Product objectives {objectives} do not overlap client objectives {client_objectives}."
    else:
        objective_result = "PASS"
        objective_reason = f"Product objectives {objectives} overlap client objectives {client_objectives}."
    factors.append(_factor(
        "objective_match", "Investment Objective Match", "SOFT",
        objective_result, objective_reason, override_permitted=True,
    ))

    limit = policy.get("concentration_limit_pct") or profile.get("max_single_stock_pct")
    aum = profile.get("aum_usd_millions")
    if amount is None or limit is None or aum is None:
        concentration_result = "MISSING"
        concentration_reason = "Concentration cannot be checked: amount, limit or client AUM is absent."
    elif amount.currency != "USD":
        concentration_result = "MISSING"
        concentration_reason = f"Concentration check needs an approved FX rate for {amount.currency}."
    else:
        position_pct = float(amount.amount) / (float(aum) * 1_000_000) * 100
        if position_pct > float(limit):
            concentration_result = "WARN"
            concentration_reason = (
                f"Position {position_pct:.2f}% of AUM exceeds the {limit}% concentration limit."
            )
        else:
            concentration_result = "PASS"
            concentration_reason = f"Position {position_pct:.2f}% of AUM is within the {limit}% limit."
    factors.append(_factor(
        "concentration_limit", "Concentration Limit", "SOFT",
        concentration_result, concentration_reason, override_permitted=True,
    ))

    return factors


RuleSet = Callable[[dict, dict, dict, Money | None, str | None], list[SuitabilityFactor]]

def evaluate_sg(
    policy: dict,
    profile: dict,
    product: dict,
    amount: Money | None,
    account_ref: str | None,
) -> list[SuitabilityFactor]:
    """MAS pack. Reuses the HK factor shape, then adds SG-only hard factors.

    An SG client must not be assessed by silently falling through to HK (B-13).
    """
    factors = list(evaluate_hk(policy, profile, product, amount, account_ref))
    vulnerable = bool(profile.get("vulnerable") or profile.get("vulnerable_client"))
    hrs = bool(profile.get("high_risk_segment") or profile.get("hrs"))
    cka_ok = profile.get("cka_passed")
    complex_product = str(product.get("complexity") or "").upper() == "COMPLEX"
    status = profile.get("investor_status")
    factors.append(_factor(
        "investor_status", "Investor status", "HARD",
        "MISSING" if not status else "PASS",
        "Accredited / retail status is missing." if not status else f"Investor status {status}.",
    ))
    factors.append(_factor(
        "cka_complex", "CKA for complex products", "HARD",
        "FAIL" if complex_product and not cka_ok else "PASS",
        "Complex product requires a current CKA." if complex_product and not cka_ok else "CKA gate passed.",
    ))
    factors.append(_factor(
        "vulnerable_client", "Vulnerable client", "HARD",
        "WARN" if vulnerable else "PASS",
        "Vulnerable client: checker required, never auto-approved." if vulnerable else "Not flagged vulnerable.",
    ))
    factors.append(_factor(
        "high_risk_segment", "High-risk segment", "HARD",
        "WARN" if hrs else "PASS",
        "High-risk segment requires a checker." if hrs else "Not a high-risk segment.",
    ))
    restricted = bool(profile.get("cross_border_restricted"))
    factors.append(_factor(
        "cross_border", "Cross-border eligibility", "HARD",
        "FAIL" if restricted else "PASS",
        "Booking centre, residence and product domicile do not match." if restricted else "Cross-border check passed.",
    ))
    factors.append(_factor(
        "unsuitable_sale", "Unsuitable sale", "SOFT",
        "PASS",
        "No unsuitable-sale flag on the profile. A RED rating still blocks hand-off.",
        override_permitted=True,
    ))
    return factors


RULE_SETS: dict[str, RuleSet] = {"HK": evaluate_hk, "SG": evaluate_sg, "SINGAPORE": evaluate_sg}


def rule_set_for(jurisdiction: str | None) -> RuleSet | None:
    """Resolve the approved rule set for a market; unknown markets stay unassessed."""
    return RULE_SETS.get((jurisdiction or "").strip().upper())
