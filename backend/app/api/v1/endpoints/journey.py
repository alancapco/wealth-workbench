"""Journey API — Engage, Discover, Recommend, Act, Service."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.journey import service as journey
from app.services.journey.logic import CATALOGUE, PIPELINE_STAGES, catalogue_search

router = APIRouter(prefix="/journey", tags=["journey"])

MAKER = journey.MAKER
CHECKER = "fixture:sales-manager@example.test"


class ControlBody(BaseModel):
    state: str = Field(pattern="^(PIN|SNOOZE|DISMISS)$")


class InvestorBody(BaseModel):
    rpq_band: str | None = None
    rpq_score: int | None = None
    rpq_answers: dict | None = None
    cka_passed: bool | None = None
    car_status: str | None = None
    investor_status: str | None = None
    accreditation_evidence: str | None = None
    expiry_date: str | None = None
    vulnerable: bool | None = None
    high_risk_segment: bool | None = None
    cross_border_restricted: bool | None = None


class FinancialBody(BaseModel):
    annual_income_band: str | None = None
    investable_assets_band: str | None = None
    liquidity_need: str | None = None
    investment_objective: str | None = None


class GoalBody(BaseModel):
    name: str
    target_usd: float
    target_date: str | None = None
    monthly_contribution_usd: float = 0
    current_usd: float = 0
    product_tags: list[str] = []


class AssistBody(BaseModel):
    transcript: str


class AcceptBody(BaseModel):
    proposals: list[dict]


class DocumentBody(BaseModel):
    file_name: str
    document_type: str = "KYC"
    note: str | None = None
    expires_on: str | None = None


class OutreachBody(BaseModel):
    client_ids: list[UUID]
    message: str


class CartItemBody(BaseModel):
    product_id: str
    amount_usd: float
    order_type: str | None = None
    side: str = "BUY"
    discount_pct: float = 0
    goal_id: str | None = None


class CartBody(BaseModel):
    client_id: UUID
    items: list[CartItemBody]


class SignBody(BaseModel):
    signer_name: str


class DecideBody(BaseModel):
    decision: str = Field(pattern="^(APPROVE|REJECT)$")
    role: str = Field(pattern="^(SALES_MANAGER|COMPLIANCE)$")
    actor: str = CHECKER
    reason: str


class StressBody(BaseModel):
    market_shock_pct: float = -10
    fx_shock_pct: float = -5
    sector_shock_pct: float = 0


class ProtectBody(BaseModel):
    question: str


class CohortBody(BaseModel):
    name: str
    filters: dict = {}


class EventBody(BaseModel):
    stage: str
    event: str
    client_id: UUID | None = None
    detail: dict = {}


class MeetingBody(BaseModel):
    title: str = "Client meeting"
    transcript: str
    consent: bool = False


class ApplyMeetingBody(BaseModel):
    accepted: list[dict] = []


class CopilotBody(BaseModel):
    question: str
    stage: str = "ENGAGE"


class PlanBody(BaseModel):
    current_age: int = 50
    retirement_age: int = 65
    current_savings_usd_millions: float = 5
    monthly_contribution_usd: float = 10000
    target_retirement_corpus_usd_millions: float = 10
    assumed_annual_return_pct: float = 6
    inflation_pct: float = 2.5


def _ok(data):
    return {"data": data, "meta": {"source": "journey"}}


@router.get("/my-day")
async def get_my_day(db: AsyncSession = Depends(get_db)):
    return _ok(await journey.my_day(db))


@router.get("/leads")
async def get_leads(db: AsyncSession = Depends(get_db)):
    return _ok(await journey.ranked_leads(db))


@router.post("/leads/{client_id}/control")
async def post_control(client_id: UUID, body: ControlBody, db: AsyncSession = Depends(get_db)):
    await journey.set_control(db, client_id, body.state)
    return _ok({"client_id": str(client_id), "state": body.state})


@router.get("/clients")
async def get_clients(
    q: str | None = None,
    jurisdiction: str | None = None,
    risk: str | None = None,
    aum_min: float | None = None,
    db: AsyncSession = Depends(get_db),
):
    rows = await journey.search_clients(db, {
        "q": q, "jurisdiction": jurisdiction, "risk": risk, "aum_min": aum_min,
    })
    return _ok(rows)


@router.get("/clients/{client_id}")
async def get_client(client_id: UUID, db: AsyncSession = Depends(get_db)):
    view = await journey.client_360(db, client_id)
    if view is None:
        raise HTTPException(404, "Client not in the journey book")
    return _ok(view)


@router.get("/clients/{client_id}/brief")
async def get_brief(client_id: UUID, db: AsyncSession = Depends(get_db)):
    brief = await journey.brief_for(db, client_id)
    if brief is None:
        raise HTTPException(404, "Client not found")
    return _ok(brief)


@router.put("/clients/{client_id}/investor-profile")
async def put_investor(client_id: UUID, body: InvestorBody, db: AsyncSession = Depends(get_db)):
    return _ok(await journey.save_investor(db, client_id, body.model_dump(exclude_unset=True)))


@router.put("/clients/{client_id}/financial-profile")
async def put_financial(client_id: UUID, body: FinancialBody, db: AsyncSession = Depends(get_db)):
    return _ok(await journey.save_financial(db, client_id, body.model_dump(exclude_unset=True)))


@router.post("/clients/{client_id}/confirm-unchanged")
async def post_confirm(client_id: UUID, db: AsyncSession = Depends(get_db)):
    return _ok(await journey.confirm_unchanged(db, client_id, MAKER))


@router.post("/clients/{client_id}/goals")
async def post_goal(client_id: UUID, body: GoalBody, db: AsyncSession = Depends(get_db)):
    return _ok(await journey.add_goal(db, client_id, body.model_dump()))


@router.post("/clients/{client_id}/assist")
async def post_assist(client_id: UUID, body: AssistBody, db: AsyncSession = Depends(get_db)):
    return _ok(await journey.assist(db, client_id, body.transcript))


@router.post("/clients/{client_id}/assist/accept")
async def post_accept(client_id: UUID, body: AcceptBody, db: AsyncSession = Depends(get_db)):
    return _ok(await journey.accept_assist(db, client_id, body.proposals))


@router.post("/clients/{client_id}/documents")
async def post_document(client_id: UUID, body: DocumentBody, db: AsyncSession = Depends(get_db)):
    return _ok(await journey.add_document(db, client_id, body.model_dump()))


@router.get("/clients/{client_id}/shortlist")
async def get_shortlist(client_id: UUID, q: str | None = None, db: AsyncSession = Depends(get_db)):
    data = await journey.shortlist(db, client_id, q)
    if data is None:
        raise HTTPException(404, "Client not found")
    return _ok(data)


@router.get("/clients/{client_id}/pitch/{product_id}")
async def get_pitch(client_id: UUID, product_id: str, db: AsyncSession = Depends(get_db)):
    data = await journey.explain(db, client_id, product_id)
    if data is None:
        raise HTTPException(404, "Product or client not found")
    return _ok(data)


@router.post("/clients/{client_id}/optimise")
async def post_optimise(client_id: UUID, db: AsyncSession = Depends(get_db)):
    data = await journey.proposal(db, client_id)
    if data is None:
        raise HTTPException(404, "Client not found")
    return _ok(data)


@router.get("/clients/{client_id}/projection")
async def get_projection(client_id: UUID, db: AsyncSession = Depends(get_db)):
    data = await journey.projection(db, client_id)
    if data is None:
        raise HTTPException(404, "Client not found")
    return _ok(data)


@router.post("/clients/{client_id}/stress")
async def post_stress(client_id: UUID, body: StressBody, db: AsyncSession = Depends(get_db)):
    data = await journey.run_stress(db, client_id, body.model_dump())
    if data is None:
        raise HTTPException(404, "Client not found")
    return _ok(data)


@router.get("/pipeline")
async def get_pipeline(db: AsyncSession = Depends(get_db)):
    return _ok(await journey.pipeline(db))


@router.post("/pipeline/{opportunity_id}/advance")
async def post_advance(opportunity_id: UUID, db: AsyncSession = Depends(get_db)):
    data = await journey.advance_opportunity(db, opportunity_id)
    if data is None:
        raise HTTPException(404, "Opportunity not found")
    return _ok(data)


@router.post("/outreach")
async def post_outreach(body: OutreachBody, db: AsyncSession = Depends(get_db)):
    return _ok(await journey.outreach(db, body.client_ids, body.message))


@router.get("/catalogue")
async def get_catalogue(q: str | None = None):
    return _ok(catalogue_search(q or ""))


@router.post("/protect")
async def post_protect(body: ProtectBody):
    return _ok(await journey.ask_policy(body.question))


@router.post("/carts")
async def post_cart(body: CartBody, db: AsyncSession = Depends(get_db)):
    data = await journey.create_cart(db, body.client_id, [item.model_dump() for item in body.items], MAKER)
    if data.get("error"):
        raise HTTPException(404, data["error"])
    return _ok(data)


@router.post("/carts/{cart_id}/sign")
async def post_sign(cart_id: UUID, body: SignBody, db: AsyncSession = Depends(get_db)):
    data = await journey.sign_cart(db, cart_id, body.signer_name)
    if data is None:
        raise HTTPException(404, "Cart not found")
    return _ok(data)


@router.post("/carts/{cart_id}/submit")
async def post_submit(cart_id: UUID, db: AsyncSession = Depends(get_db)):
    data = await journey.submit_cart(db, cart_id, MAKER)
    if data is None:
        raise HTTPException(404, "Cart not found")
    return _ok(data)


@router.get("/approvals")
async def get_approvals(db: AsyncSession = Depends(get_db)):
    return _ok(await journey.list_approvals(db))


@router.post("/approvals/{approval_id}/decide")
async def post_decide(approval_id: UUID, body: DecideBody, db: AsyncSession = Depends(get_db)):
    return _ok(await journey.decide_approval(db, approval_id, body.actor, body.role, body.decision, body.reason))


@router.get("/notifications")
async def get_notes(db: AsyncSession = Depends(get_db)):
    return _ok(await journey.list_notifications(db))


@router.post("/notifications/{note_id}/read")
async def post_read(note_id: UUID, db: AsyncSession = Depends(get_db)):
    await journey.mark_read(db, note_id)
    return _ok({"id": str(note_id), "read": True})


@router.post("/evaluate")
async def post_evaluate(db: AsyncSession = Depends(get_db)):
    return _ok(await journey.evaluate_book(db))


@router.post("/cohorts")
async def post_cohort(body: CohortBody, db: AsyncSession = Depends(get_db)):
    return _ok(await journey.save_cohort(db, body.name, body.filters))


@router.post("/events")
async def post_event(body: EventBody, db: AsyncSession = Depends(get_db)):
    await journey.record_event(db, body.stage, body.event, body.client_id, body.detail)
    await db.commit()
    return _ok({"recorded": True, "stage": body.stage, "event": body.event})


@router.get("/clients/{client_id}/meetings/sample")
async def get_meeting_sample(client_id: UUID, db: AsyncSession = Depends(get_db)):
    from app.services.journey.meeting_ai import sample_for

    client = await journey._client(db, client_id)
    if client is None:
        raise HTTPException(404, "Client not found")
    return _ok(sample_for(f"{client.firstname} {client.lastname}"))


@router.post("/clients/{client_id}/meetings/summarise")
async def post_meeting(client_id: UUID, body: MeetingBody, db: AsyncSession = Depends(get_db)):
    from app.services.journey.meeting_ai import summarise

    client = await journey._client(db, client_id)
    if client is None:
        raise HTTPException(404, "Client not found")
    result = await summarise(db, client, body.title, body.transcript, body.consent)
    if not result.get("ok"):
        raise HTTPException(400, result.get("reason") or "Meeting was not summarised")
    return _ok(result)


@router.post("/clients/{client_id}/meetings/{meeting_id}/apply")
async def post_apply_meeting(client_id: UUID, meeting_id: UUID, body: ApplyMeetingBody, db: AsyncSession = Depends(get_db)):
    from app.services.journey.meeting_ai import apply_updates

    result = await apply_updates(db, client_id, meeting_id, body.accepted)
    if not result.get("ok"):
        raise HTTPException(404, result.get("reason") or "Meeting not found")
    return _ok(result)


@router.post("/clients/{client_id}/copilot")
async def post_copilot(client_id: UUID, body: CopilotBody, db: AsyncSession = Depends(get_db)):
    result = await journey.copilot(db, client_id, body.question, body.stage)
    if result is None:
        raise HTTPException(404, "Client not found")
    return _ok(result)


@router.post("/clients/{client_id}/plan")
async def post_plan(client_id: UUID, body: PlanBody, db: AsyncSession = Depends(get_db)):
    client = await journey._client(db, client_id)
    if client is None:
        raise HTTPException(404, "Client not found")
    from app.api.v1.endpoints.demo_clients import _plan_narrative
    from app.services.planning.projection import project_plan

    report = project_plan(**body.model_dump())
    report.update(await _plan_narrative(f"{client.firstname} {client.lastname}", report, client.risk_profile or "Moderate"))
    return _ok(report)


@router.get("/roles")
async def get_roles():
    return _ok({
        "maker": {"subject": MAKER, "role": "RM"},
        "checker": {"subject": CHECKER, "role": "SALES_MANAGER"},
        "compliance": {"subject": "fixture:compliance@example.test", "role": "COMPLIANCE"},
        "rule": "Maker cannot decide their own approval.",
        "stages": PIPELINE_STAGES,
        "catalogue_size": len(CATALOGUE),
    })
