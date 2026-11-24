"""Suitability assessment service - automated match, conflict detection, explainability.

Architecture §6.7 API-061 - assess product suitability against current profile.
Pre-screen only, not compliance approval. Missing/expired profile blocks GREEN rating.
"""
from dataclasses import dataclass, field
from datetime import date, datetime, UTC
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client_data import ClientSuitabilityProfile, DemoClient
from app.models.models import Client
from app.schemas.common import (
    Blocker,
    BlockerResolution,
    ConfigRef,
    Environment,
    EnvironmentKind,
    Money,
)
from app.schemas.product import (
    Assessment,
    ProductRef,
    ProfileValidity,
    SuitabilityFactor,
    SuitabilityRating,
)
from app.services.product.config_refs import (
    POLICY_CONFIG_KEY,
    canonical_hash,
    jurisdiction_code,
    unconfigured_config_ref,
)
from app.services.product.rule_sets import rule_set_for
from app.services.product.search_service import ProductSearchService


@dataclass
class ProfileSnapshot:
    validity: ProfileValidity
    reason: str
    id: str | None = None
    version: str | None = None
    jurisdiction: str | None = None
    data: dict = field(default_factory=dict)


class SuitabilityService:
    """Suitability assessment - automated conflict detection with explainability."""

    def __init__(
        self,
        policy_ref: ConfigRef | None,
        db: AsyncSession | None = None,
        policy: dict | None = None,
        jurisdiction: str | None = None,
        policy_reason: str | None = None,
        environment: Environment | None = None,
    ):
        self.policy_ref = policy_ref
        self.db = db
        self.policy = policy or {}
        self.jurisdiction = jurisdiction
        self.policy_reason = policy_reason
        self.environment = environment or Environment(kind=EnvironmentKind.FIXTURE, id="test")
        self._profile: ProfileSnapshot | None = None
        self._product_record: dict | None = None

    async def assess_suitability(
        self,
        tenant_id: str,
        client_id: UUID,
        product_ref: ProductRef,
        account_ref: str | None,
        amount: Money | None,
    ) -> Assessment:
        """Assess product suitability against the current client profile.

        GREEN means no detected conflict, not compliance approval. An unknown
        policy, unknown jurisdiction, unknown product or a non-current KYC
        profile can never produce GREEN.
        """
        inputs = self._decision_inputs(client_id, product_ref, account_ref, amount)
        profile_validity = await self._check_profile_validity(tenant_id, client_id)
        profile = await self._load_profile(tenant_id, client_id)
        inputs["profile"] = self._profile_inputs(profile)
        jurisdiction = self.jurisdiction or profile.jurisdiction
        inputs["jurisdiction"] = jurisdiction

        if self.policy_ref is None:
            reason = self.policy_reason or (
                "No approved suitability policy is configured for this tenant/jurisdiction."
            )
            ref = unconfigured_config_ref(tenant_id, POLICY_CONFIG_KEY, reason)
            return Assessment(
                client_id=client_id,
                product_ref=product_ref,
                account_ref=account_ref,
                amount=amount,
                profile_id=profile.id,
                profile_version=profile.version,
                profile_validity=profile.validity,
                input_hash=self._compute_input_hash(inputs),
                policy_ref=ref,
                rating="UNAVAILABLE",
                current=True,
                factors=[SuitabilityFactor(
                    key="policy_availability",
                    label="Approved Suitability Policy",
                    classification="UNKNOWN",
                    result="MISSING",
                    evidence_refs=[],
                    explanation=reason,
                    override_permitted=False,
                )],
                ticket_eligible=False,
                blockers=[Blocker(
                    code="SUITABILITY_POLICY_UNCONFIGURED",
                    field="policy_ref",
                    config_ref=None,
                    resolution=BlockerResolution.ADMIN,
                )],
                assessed_at=datetime.now(UTC),
            )

        rule_key = self.policy.get("rule_set") or jurisdiction
        rule_set = rule_set_for(rule_key)
        if rule_set is None:
            return self._unavailable(
                client_id, product_ref, account_ref, amount, profile, inputs,
                "SUITABILITY_RULE_SET_UNAVAILABLE",
                f"No approved suitability rule set for jurisdiction {rule_key or 'UNKNOWN'}.",
            )

        if profile_validity != "CURRENT":
            return Assessment(
                client_id=client_id,
                product_ref=product_ref,
                account_ref=account_ref,
                amount=amount,
                profile_id=profile.id,
                profile_version=profile.version,
                profile_validity=profile.validity,
                input_hash=self._compute_input_hash(inputs),
                policy_ref=self.policy_ref,
                rating="RED",
                current=True,
                factors=[SuitabilityFactor(
                    key="profile_validity",
                    label="Current KYC/Profile Required",
                    classification="HARD",
                    result="FAIL",
                    evidence_refs=[],
                    explanation=f"Profile status: {profile.validity}. {profile.reason}",
                    override_permitted=False,
                )],
                ticket_eligible=False,
                blockers=[Blocker(
                    code="PROFILE_MISSING_OR_EXPIRED",
                    field="profile",
                    config_ref=None,
                    resolution=BlockerResolution.ADMIN,
                )],
                assessed_at=datetime.now(UTC),
            )

        product = await self._load_product(tenant_id, client_id, product_ref, jurisdiction)
        if product is None:
            return self._unavailable(
                client_id, product_ref, account_ref, amount, profile, inputs,
                "PRODUCT_NOT_IN_APPROVED_UNIVERSE",
                "Product is not in the current approved entitled universe; suitability cannot be assessed.",
            )
        inputs["product"] = product
        self._product_record = product

        factors = await self._evaluate_factors(
            tenant_id, client_id, product_ref, account_ref, amount
        )
        rating = self._compute_rating(factors)
        # A HARD factor that is FAIL or only MISSING must not be ticket-eligible (B-14).
        hard_blocks_ticket = any(
            factor.classification == "HARD" and factor.result in ("FAIL", "MISSING")
            for factor in factors
        )
        ticket_eligible = (
            rating in ("GREEN", "YELLOW")
            and profile_validity == "CURRENT"
            and not hard_blocks_ticket
        )

        blockers = []
        if not ticket_eligible:
            blockers.append(Blocker(
                code="TICKET_NOT_ELIGIBLE",
                field=None,
                config_ref=None,
                resolution=BlockerResolution.REVIEW if rating == "YELLOW" else BlockerResolution.ADMIN,
            ))

        return Assessment(
            client_id=client_id,
            product_ref=product_ref,
            account_ref=account_ref,
            amount=amount,
            profile_id=profile.id,
            profile_version=profile.version,
            profile_validity=profile.validity,
            input_hash=self._compute_input_hash(inputs),
            policy_ref=self.policy_ref,
            rating=rating,
            current=True,
            factors=factors,
            ticket_eligible=ticket_eligible,
            blockers=blockers,
            assessed_at=datetime.now(UTC),
        )

    def _unavailable(
        self,
        client_id: UUID,
        product_ref: ProductRef,
        account_ref: str | None,
        amount: Money | None,
        profile: ProfileSnapshot,
        inputs: dict,
        code: str,
        reason: str,
    ) -> Assessment:
        return Assessment(
            client_id=client_id,
            product_ref=product_ref,
            account_ref=account_ref,
            amount=amount,
            profile_id=profile.id,
            profile_version=profile.version,
            profile_validity=profile.validity,
            input_hash=self._compute_input_hash(inputs),
            policy_ref=self.policy_ref,
            rating="UNAVAILABLE",
            current=True,
            factors=[SuitabilityFactor(
                key="assessment_availability",
                label="Assessment Availability",
                classification="UNKNOWN",
                result="MISSING",
                evidence_refs=[],
                explanation=reason,
                override_permitted=False,
            )],
            ticket_eligible=False,
            blockers=[Blocker(
                code=code,
                field=None,
                config_ref=None,
                resolution=BlockerResolution.ADMIN,
            )],
            assessed_at=datetime.now(UTC),
        )

    def _decision_inputs(
        self,
        client_id: UUID,
        product_ref: ProductRef,
        account_ref: str | None,
        amount: Money | None,
    ) -> dict:
        return {
            "client_id": str(client_id),
            "product_ref": product_ref.model_dump(),
            "account_ref": account_ref,
            "amount": amount.model_dump() if amount else None,
            "policy_ref": self.policy_ref.model_dump(mode="json") if self.policy_ref else None,
            "policy_reason": self.policy_reason,
            "policy": self.policy,
            "jurisdiction": self.jurisdiction,
            "profile": None,
            "product": None,
        }

    @staticmethod
    def _profile_inputs(profile: ProfileSnapshot) -> dict:
        return {
            "id": profile.id,
            "version": profile.version,
            "validity": profile.validity,
            "jurisdiction": profile.jurisdiction,
            **profile.data,
        }

    async def _load_profile(self, tenant_id: str, client_id: UUID) -> ProfileSnapshot:
        """Read the real KYC record once per assessment and cache the snapshot."""
        if self._profile is None:
            self._profile = await self._query_profile(client_id)
        return self._profile

    async def _query_profile(self, client_id: UUID) -> ProfileSnapshot:
        """Read the real KYC record and its freshness/conflict state."""
        if self.db is None:
            return ProfileSnapshot("MISSING", "No KYC data source is available to this assessment.")
        try:
            kyc = (await self.db.execute(
                select(ClientSuitabilityProfile).where(ClientSuitabilityProfile.client_id == client_id)
            )).scalar_one_or_none()
            client = (await self.db.execute(
                select(Client).where(Client.id == client_id)
            )).scalar_one_or_none()
            demo = (await self.db.execute(
                select(DemoClient).where(DemoClient.id == client_id)
            )).scalar_one_or_none()
        except Exception as exc:
            return ProfileSnapshot("MISSING", f"KYC/profile data could not be read: {type(exc).__name__}")

        preferences = client.preferences if client and isinstance(client.preferences, dict) else {}
        country = (demo.country if demo else None) or (client.region if client else None)
        aum = demo.aum_usd_millions if demo and demo.aum_usd_millions else (
            client.aum / 1_000_000 if client and client.aum else None
        )
        data = {
            "risk_tolerance": (kyc.risk_tolerance if kyc else None) or (client.risk_profile if client else None),
            "investment_horizon_years": kyc.investment_horizon_years if kyc else None,
            "liquidity_needs": kyc.liquidity_needs if kyc else None,
            "max_single_stock_pct": kyc.max_single_stock_pct if kyc else None,
            "investment_objectives": preferences.get("investment_objectives") or [],
            "complexity_acknowledged": preferences.get("complexity_acknowledged")
            or preferences.get("investment_experience"),
            "aum_usd_millions": aum,
            "country": country,
        }
        jurisdiction = jurisdiction_code(country)
        scale = self.policy.get("risk_scale") or {}

        if kyc is not None:
            profile_id = str(kyc.id)
            profile_version = str(kyc.profile_date) if kyc.profile_date else None
            today = date.today()
            if kyc.is_expired or (kyc.expiry_date and kyc.expiry_date < today):
                return ProfileSnapshot("EXPIRED", "KYC profile expiry date has passed.", profile_id, profile_version, jurisdiction, data)
            if kyc.profile_date and self.policy.get("profile_max_age_days"):
                age = (today - kyc.profile_date).days
                if age > int(self.policy["profile_max_age_days"]):
                    return ProfileSnapshot("EXPIRED", f"KYC profile is {age} days old, exceeding the approved maximum.", profile_id, profile_version, jurisdiction, data)
            if not kyc.risk_tolerance or not kyc.profile_date:
                return ProfileSnapshot("MISSING", "KYC profile is missing risk tolerance or profile date.", profile_id, profile_version, jurisdiction, data)
            if client and client.risk_profile and scale:
                kyc_rank = scale.get(str(kyc.risk_tolerance).strip().upper())
                client_rank = scale.get(str(client.risk_profile).strip().upper())
                if kyc_rank is not None and client_rank is not None and kyc_rank != client_rank:
                    return ProfileSnapshot("CONFLICT", "KYC risk tolerance conflicts with the client master risk profile.", profile_id, profile_version, jurisdiction, data)
            return ProfileSnapshot("CURRENT", "KYC profile is current.", profile_id, profile_version, jurisdiction, data)

        # Legacy KYC carrier: the client master record with an explicit suitability expiry.
        if client is not None and client.risk_profile and preferences.get("suitability_expiry"):
            expiry = preferences["suitability_expiry"]
            try:
                expired = date.fromisoformat(str(expiry)) < date.today()
            except ValueError:
                return ProfileSnapshot("MISSING", "Client suitability expiry is not a valid date.", str(client.id), str(expiry), jurisdiction, data)
            if expired:
                return ProfileSnapshot("EXPIRED", f"Client suitability expired on {expiry}.", str(client.id), str(expiry), jurisdiction, data)
            return ProfileSnapshot("CURRENT", "Client suitability is current.", str(client.id), str(expiry), jurisdiction, data)

        return ProfileSnapshot(
            "MISSING",
            "No KYC/suitability profile with a verifiable freshness date exists for this client.",
            None, None, jurisdiction, data,
        )

    async def _check_profile_validity(
        self,
        tenant_id: str,
        client_id: UUID,
    ) -> ProfileValidity:
        """Public KYC freshness check used by the assessment gate."""
        return (await self._load_profile(tenant_id, client_id)).validity

    async def _load_product(
        self,
        tenant_id: str,
        client_id: UUID,
        product_ref: ProductRef,
        jurisdiction: str | None,
    ) -> dict | None:
        catalog = ProductSearchService(self.environment, self.db)
        return await catalog.get_product_record(tenant_id, client_id, product_ref, jurisdiction)

    async def _evaluate_factors(
        self,
        tenant_id: str,
        client_id: UUID,
        product_ref: ProductRef,
        account_ref: str | None,
        amount: Money | None,
    ) -> list[SuitabilityFactor]:
        """Evaluate the jurisdiction rule set against real profile/product data."""
        profile = self._profile or await self._load_profile(tenant_id, client_id)
        product = self._product_record
        if product is None:
            jurisdiction = self.jurisdiction or profile.jurisdiction
            product = await self._load_product(tenant_id, client_id, product_ref, jurisdiction)
        rule_key = self.policy.get("rule_set") or self.jurisdiction or profile.jurisdiction
        rule_set = rule_set_for(rule_key)
        if rule_set is None or product is None or profile.validity != "CURRENT":
            return [SuitabilityFactor(
                key="assessment_inputs",
                label="Suitability Decision Inputs",
                classification="UNKNOWN",
                result="MISSING",
                evidence_refs=[],
                explanation="Approved rule set, current profile or product record is unavailable.",
                override_permitted=False,
            )]
        return rule_set(self.policy, profile.data, product, amount, account_ref)

    def _compute_rating(self, factors: list[SuitabilityFactor]) -> SuitabilityRating:
        """Compute overall rating from factor results."""
        # No evaluated factors means no evidence; never infer a clean bill.
        if not factors:
            return "UNAVAILABLE"
        for factor in factors:
            if factor.classification == "HARD" and factor.result == "FAIL":
                return "RED"
        for factor in factors:
            if factor.result in ["FAIL", "WARN", "MISSING"]:
                return "YELLOW"
        return "GREEN"

    @staticmethod
    def _compute_input_hash(inputs: dict) -> str:
        """Hash every decision input so policy/profile/product changes are visible."""
        return canonical_hash(inputs)
