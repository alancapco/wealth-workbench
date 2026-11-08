"""
Seed script for DemoClient + ClientPortfolioHolding.

Run: cd backend && uv run python -m app.scripts.seed_demo_holdings
"""
import asyncio
from datetime import date

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models.client_data import ClientPortfolioHolding, DemoClient

AS_OF = date(2026, 11, 8)


CLIENTS = [
    {
        "firstname": "Kenneth",
        "lastname": "Wong",
        "email": "kenneth.wong@capcodemo.com",
        "phone": "+852-9123-4567",
        "city": "Hong Kong",
        "country": "Hong Kong",
        "ethnicity": "Chinese",
        "religion": None,
        "language_preference": "English",
        "aum_usd_millions": 45.2,
        "client_segment": "HNW",
        "risk_profile": "Moderate",
        "portfolio_type": "Equities Heavy",
        "shariah_compliant": False,
        "family_office_name": None,
        "family_role": None,
        "holdings": [
            {"asset_class": "Equities", "asset_name": "HSBC Holdings", "ticker": "0005.HK", "value_usd_millions": 9.5, "allocation_pct": 21.0, "unrealized_gain_pct": 6.2, "currency": "HKD", "is_shariah_compliant": False},
            {"asset_class": "Equities", "asset_name": "Tencent Holdings", "ticker": "0700.HK", "value_usd_millions": 7.8, "allocation_pct": 17.3, "unrealized_gain_pct": -3.1, "currency": "HKD", "is_shariah_compliant": False},
            {"asset_class": "Equities", "asset_name": "Apple Inc", "ticker": "AAPL", "value_usd_millions": 6.2, "allocation_pct": 13.7, "unrealized_gain_pct": 18.4, "currency": "USD", "is_shariah_compliant": False},
            {"asset_class": "Fixed Income", "asset_name": "US Treasury 10Y", "ticker": "TLT", "value_usd_millions": 8.1, "allocation_pct": 17.9, "unrealized_gain_pct": -2.5, "currency": "USD", "is_shariah_compliant": False},
            {"asset_class": "Alternatives", "asset_name": "Blackstone Real Estate Fund", "ticker": None, "value_usd_millions": 9.4, "allocation_pct": 20.8, "unrealized_gain_pct": 11.3, "currency": "USD", "is_shariah_compliant": False},
            {"asset_class": "Cash", "asset_name": "HKD Money Market", "ticker": None, "value_usd_millions": 4.2, "allocation_pct": 9.3, "unrealized_gain_pct": 0.0, "currency": "HKD", "is_shariah_compliant": False},
        ],
    },
    {
        "firstname": "Ahmad",
        "lastname": "Rahman",
        "email": "ahmad.rahman@capcodemo.com",
        "phone": "+65-9234-5678",
        "city": "Singapore",
        "country": "Singapore",
        "ethnicity": "Malay",
        "religion": "Islam",
        "language_preference": "English",
        "aum_usd_millions": 32.8,
        "client_segment": "HNW",
        "risk_profile": "Conservative",
        "portfolio_type": "Shariah Balanced",
        "shariah_compliant": True,
        "family_office_name": None,
        "family_role": None,
        "holdings": [
            {"asset_class": "Equities", "asset_name": "Saudi Aramco", "ticker": "2222.SR", "value_usd_millions": 6.5, "allocation_pct": 19.8, "unrealized_gain_pct": 4.1, "currency": "USD", "is_shariah_compliant": True},
            {"asset_class": "Equities", "asset_name": "Emirates NBD Bank", "ticker": "ENBD.DU", "value_usd_millions": 4.9, "allocation_pct": 14.9, "unrealized_gain_pct": 7.8, "currency": "USD", "is_shariah_compliant": True},
            {"asset_class": "Fixed Income", "asset_name": "Malaysia Sukuk 5Y", "ticker": None, "value_usd_millions": 8.2, "allocation_pct": 25.0, "unrealized_gain_pct": 1.2, "currency": "SGD", "is_shariah_compliant": True},
            {"asset_class": "Fixed Income", "asset_name": "Singapore Sukuk Fund", "ticker": None, "value_usd_millions": 6.0, "allocation_pct": 18.3, "unrealized_gain_pct": 0.8, "currency": "SGD", "is_shariah_compliant": True},
            {"asset_class": "Real Estate", "asset_name": "Sabana REIT (Shariah)", "ticker": "M1GU.SI", "value_usd_millions": 4.2, "allocation_pct": 12.8, "unrealized_gain_pct": -1.5, "currency": "SGD", "is_shariah_compliant": True},
            {"asset_class": "Cash", "asset_name": "SGD Murabahah Deposit", "ticker": None, "value_usd_millions": 3.0, "allocation_pct": 9.1, "unrealized_gain_pct": 0.0, "currency": "SGD", "is_shariah_compliant": True},
        ],
    },
    {
        "firstname": "Tan",
        "lastname": "Family Office",
        "email": "office@tanfamilyoffice.capcodemo.com",
        "phone": "+65-6345-6789",
        "city": "Singapore",
        "country": "Singapore",
        "ethnicity": "Chinese",
        "religion": None,
        "language_preference": "English",
        "aum_usd_millions": 120.5,
        "client_segment": "UHNW",
        "risk_profile": "Balanced",
        "portfolio_type": "Diversified Multi-Asset",
        "shariah_compliant": False,
        "family_office_name": "Tan Family Office Pte Ltd",
        "family_role": "Principal",
        "holdings": [
            {"asset_class": "Equities", "asset_name": "S&P 500 Index Fund", "ticker": "SPY", "value_usd_millions": 24.1, "allocation_pct": 20.0, "unrealized_gain_pct": 14.2, "currency": "USD", "is_shariah_compliant": False},
            {"asset_class": "Equities", "asset_name": "DBS Group Holdings", "ticker": "D05.SI", "value_usd_millions": 18.0, "allocation_pct": 15.0, "unrealized_gain_pct": 9.7, "currency": "SGD", "is_shariah_compliant": False},
            {"asset_class": "Equities", "asset_name": "HSBC Holdings", "ticker": "0005.HK", "value_usd_millions": 12.0, "allocation_pct": 10.0, "unrealized_gain_pct": 5.1, "currency": "HKD", "is_shariah_compliant": False},
            {"asset_class": "Fixed Income", "asset_name": "Singapore Govt Bond 10Y", "ticker": None, "value_usd_millions": 18.0, "allocation_pct": 15.0, "unrealized_gain_pct": -0.8, "currency": "SGD", "is_shariah_compliant": False},
            {"asset_class": "Fixed Income", "asset_name": "US Corporate Bond Fund", "ticker": "LQD", "value_usd_millions": 14.4, "allocation_pct": 12.0, "unrealized_gain_pct": 2.1, "currency": "USD", "is_shariah_compliant": False},
            {"asset_class": "Real Estate", "asset_name": "CapitaLand REIT", "ticker": "C38U.SI", "value_usd_millions": 15.6, "allocation_pct": 13.0, "unrealized_gain_pct": 3.4, "currency": "SGD", "is_shariah_compliant": False},
            {"asset_class": "Alternatives", "asset_name": "KKR Global Infrastructure", "ticker": None, "value_usd_millions": 12.0, "allocation_pct": 10.0, "unrealized_gain_pct": 16.5, "currency": "USD", "is_shariah_compliant": False},
            {"asset_class": "Cash", "asset_name": "Multi-Currency Cash Pool", "ticker": None, "value_usd_millions": 6.4, "allocation_pct": 5.0, "unrealized_gain_pct": 0.0, "currency": "SGD", "is_shariah_compliant": False},
        ],
    },
    {
        "firstname": "Li",
        "lastname": "Wei",
        "email": "li.wei@capcodemo.com",
        "phone": "+86-138-0013-8000",
        "city": "Shanghai",
        "country": "China",
        "ethnicity": "Chinese",
        "religion": None,
        "language_preference": "Mandarin",
        "aum_usd_millions": 18.0,
        "client_segment": "HNW",
        "risk_profile": "Aggressive",
        "portfolio_type": "Tech Heavy",
        "shariah_compliant": False,
        "family_office_name": None,
        "family_role": None,
        "holdings": [
            {"asset_class": "Equities", "asset_name": "Alibaba Group", "ticker": "BABA", "value_usd_millions": 4.5, "allocation_pct": 25.0, "unrealized_gain_pct": -12.3, "currency": "USD", "is_shariah_compliant": False},
            {"asset_class": "Equities", "asset_name": "BYD Company", "ticker": "002594.SZ", "value_usd_millions": 3.6, "allocation_pct": 20.0, "unrealized_gain_pct": 22.7, "currency": "CNY", "is_shariah_compliant": False},
            {"asset_class": "Equities", "asset_name": "NVIDIA Corporation", "ticker": "NVDA", "value_usd_millions": 3.2, "allocation_pct": 17.8, "unrealized_gain_pct": 41.5, "currency": "USD", "is_shariah_compliant": False},
            {"asset_class": "Equities", "asset_name": "Meituan", "ticker": "3690.HK", "value_usd_millions": 2.5, "allocation_pct": 13.9, "unrealized_gain_pct": -8.1, "currency": "HKD", "is_shariah_compliant": False},
            {"asset_class": "Fixed Income", "asset_name": "China Govt Bond 5Y", "ticker": None, "value_usd_millions": 2.2, "allocation_pct": 12.2, "unrealized_gain_pct": 1.5, "currency": "CNY", "is_shariah_compliant": False},
            {"asset_class": "Cash", "asset_name": "USD Cash Account", "ticker": None, "value_usd_millions": 2.0, "allocation_pct": 11.1, "unrealized_gain_pct": 0.0, "currency": "USD", "is_shariah_compliant": False},
        ],
    },
    {
        "firstname": "Yuki",
        "lastname": "Tanaka",
        "email": "yuki.tanaka@capcodemo.com",
        "phone": "+81-3-1234-5678",
        "city": "Tokyo",
        "country": "Japan",
        "ethnicity": "Japanese",
        "religion": None,
        "language_preference": "Japanese",
        "aum_usd_millions": 28.0,
        "client_segment": "HNW",
        "risk_profile": "Moderate",
        "portfolio_type": "Balanced Japan Exposure",
        "shariah_compliant": False,
        "family_office_name": None,
        "family_role": None,
        "holdings": [
            {"asset_class": "Equities", "asset_name": "Toyota Motor Corp", "ticker": "7203.T", "value_usd_millions": 5.6, "allocation_pct": 20.0, "unrealized_gain_pct": 8.3, "currency": "JPY", "is_shariah_compliant": False},
            {"asset_class": "Equities", "asset_name": "Sony Group Corp", "ticker": "6758.T", "value_usd_millions": 4.2, "allocation_pct": 15.0, "unrealized_gain_pct": 12.1, "currency": "JPY", "is_shariah_compliant": False},
            {"asset_class": "Equities", "asset_name": "MSCI World ETF", "ticker": "IWDA.L", "value_usd_millions": 5.0, "allocation_pct": 17.9, "unrealized_gain_pct": 9.8, "currency": "USD", "is_shariah_compliant": False},
            {"asset_class": "Fixed Income", "asset_name": "Japan Govt Bond 10Y", "ticker": None, "value_usd_millions": 7.0, "allocation_pct": 25.0, "unrealized_gain_pct": -1.2, "currency": "JPY", "is_shariah_compliant": False},
            {"asset_class": "Fixed Income", "asset_name": "US Treasury 5Y", "ticker": None, "value_usd_millions": 3.4, "allocation_pct": 12.1, "unrealized_gain_pct": -0.5, "currency": "USD", "is_shariah_compliant": False},
            {"asset_class": "Cash", "asset_name": "JPY Savings Account", "ticker": None, "value_usd_millions": 2.8, "allocation_pct": 10.0, "unrealized_gain_pct": 0.0, "currency": "JPY", "is_shariah_compliant": False},
        ],
    },
    {
        "firstname": "Priya",
        "lastname": "Sharma",
        "email": "priya.sharma@capcodemo.com",
        "phone": "+852-9456-7890",
        "city": "Hong Kong",
        "country": "Hong Kong",
        "ethnicity": "Indian",
        "religion": None,
        "language_preference": "English",
        "aum_usd_millions": 55.0,
        "client_segment": "UHNW",
        "risk_profile": "Moderate",
        "portfolio_type": "Global Diversified",
        "shariah_compliant": False,
        "family_office_name": None,
        "family_role": None,
        "holdings": [
            {"asset_class": "Equities", "asset_name": "S&P 500 Index Fund", "ticker": "SPY", "value_usd_millions": 11.0, "allocation_pct": 20.0, "unrealized_gain_pct": 15.6, "currency": "USD", "is_shariah_compliant": False},
            {"asset_class": "Equities", "asset_name": "FTSE 100 ETF", "ticker": "ISF.L", "value_usd_millions": 8.2, "allocation_pct": 14.9, "unrealized_gain_pct": 4.2, "currency": "GBP", "is_shariah_compliant": False},
            {"asset_class": "Equities", "asset_name": "Hang Seng Index ETF", "ticker": "2800.HK", "value_usd_millions": 7.7, "allocation_pct": 14.0, "unrealized_gain_pct": -5.3, "currency": "HKD", "is_shariah_compliant": False},
            {"asset_class": "Fixed Income", "asset_name": "UK Gilt 10Y", "ticker": None, "value_usd_millions": 9.9, "allocation_pct": 18.0, "unrealized_gain_pct": -3.1, "currency": "GBP", "is_shariah_compliant": False},
            {"asset_class": "Fixed Income", "asset_name": "US High Yield Bond Fund", "ticker": "HYG", "value_usd_millions": 7.7, "allocation_pct": 14.0, "unrealized_gain_pct": 3.8, "currency": "USD", "is_shariah_compliant": False},
            {"asset_class": "Real Estate", "asset_name": "Link REIT", "ticker": "0823.HK", "value_usd_millions": 6.6, "allocation_pct": 12.0, "unrealized_gain_pct": 2.9, "currency": "HKD", "is_shariah_compliant": False},
            {"asset_class": "Cash", "asset_name": "Multi-Currency Liquidity Pool", "ticker": None, "value_usd_millions": 3.9, "allocation_pct": 7.1, "unrealized_gain_pct": 0.0, "currency": "USD", "is_shariah_compliant": False},
        ],
    },
    {
        "firstname": "James",
        "lastname": "Wilson",
        "email": "james.wilson@capcodemo.com",
        "phone": "+61-2-9876-5432",
        "city": "Sydney",
        "country": "Australia",
        "ethnicity": "Caucasian",
        "religion": None,
        "language_preference": "English",
        "aum_usd_millions": 38.0,
        "client_segment": "HNW",
        "risk_profile": "Conservative",
        "portfolio_type": "Income Focused",
        "shariah_compliant": False,
        "family_office_name": None,
        "family_role": None,
        "holdings": [
            {"asset_class": "Fixed Income", "asset_name": "Australian Govt Bond 10Y", "ticker": None, "value_usd_millions": 9.5, "allocation_pct": 25.0, "unrealized_gain_pct": 0.4, "currency": "AUD", "is_shariah_compliant": False},
            {"asset_class": "Fixed Income", "asset_name": "US Treasury Bond Fund", "ticker": "BND", "value_usd_millions": 7.6, "allocation_pct": 20.0, "unrealized_gain_pct": -1.1, "currency": "USD", "is_shariah_compliant": False},
            {"asset_class": "Equities", "asset_name": "Commonwealth Bank of Australia", "ticker": "CBA.AX", "value_usd_millions": 7.2, "allocation_pct": 18.9, "unrealized_gain_pct": 11.2, "currency": "AUD", "is_shariah_compliant": False},
            {"asset_class": "Real Estate", "asset_name": "Goodman Group REIT", "ticker": "GMG.AX", "value_usd_millions": 5.7, "allocation_pct": 15.0, "unrealized_gain_pct": 7.6, "currency": "AUD", "is_shariah_compliant": False},
            {"asset_class": "Equities", "asset_name": "BHP Group", "ticker": "BHP.AX", "value_usd_millions": 4.6, "allocation_pct": 12.1, "unrealized_gain_pct": 3.8, "currency": "AUD", "is_shariah_compliant": False},
            {"asset_class": "Cash", "asset_name": "AUD Term Deposit", "ticker": None, "value_usd_millions": 3.4, "allocation_pct": 9.0, "unrealized_gain_pct": 0.0, "currency": "AUD", "is_shariah_compliant": False},
        ],
    },
    {
        "firstname": "Chen",
        "lastname": "Wei",
        "email": "chen.wei@capcodemo.com",
        "phone": "+852-9678-9012",
        "city": "Hong Kong",
        "country": "Hong Kong",
        "ethnicity": "Chinese",
        "religion": None,
        "language_preference": "Cantonese",
        "aum_usd_millions": 75.0,
        "client_segment": "UHNW",
        "risk_profile": "Aggressive",
        "portfolio_type": "Family Office Multi-Asset",
        "shariah_compliant": False,
        "family_office_name": "Chen Family Holdings Ltd",
        "family_role": "Patriarch",
        "holdings": [
            {"asset_class": "Equities", "asset_name": "Ping An Insurance", "ticker": "2318.HK", "value_usd_millions": 15.0, "allocation_pct": 20.0, "unrealized_gain_pct": -7.4, "currency": "HKD", "is_shariah_compliant": False},
            {"asset_class": "Equities", "asset_name": "Alibaba Group (HK)", "ticker": "9988.HK", "value_usd_millions": 11.2, "allocation_pct": 14.9, "unrealized_gain_pct": -14.2, "currency": "HKD", "is_shariah_compliant": False},
            {"asset_class": "Equities", "asset_name": "Tesla Inc", "ticker": "TSLA", "value_usd_millions": 9.0, "allocation_pct": 12.0, "unrealized_gain_pct": 23.5, "currency": "USD", "is_shariah_compliant": False},
            {"asset_class": "Alternatives", "asset_name": "Carlyle Asia PE Fund", "ticker": None, "value_usd_millions": 12.0, "allocation_pct": 16.0, "unrealized_gain_pct": 18.9, "currency": "USD", "is_shariah_compliant": False},
            {"asset_class": "Real Estate", "asset_name": "HK Residential Portfolio", "ticker": None, "value_usd_millions": 13.5, "allocation_pct": 18.0, "unrealized_gain_pct": 5.2, "currency": "HKD", "is_shariah_compliant": False},
            {"asset_class": "Fixed Income", "asset_name": "China Development Bank Bond", "ticker": None, "value_usd_millions": 9.0, "allocation_pct": 12.0, "unrealized_gain_pct": 2.1, "currency": "CNY", "is_shariah_compliant": False},
            {"asset_class": "Cash", "asset_name": "HKD / USD Cash Reserves", "ticker": None, "value_usd_millions": 5.3, "allocation_pct": 7.1, "unrealized_gain_pct": 0.0, "currency": "HKD", "is_shariah_compliant": False},
        ],
    },
]


def _async_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


async def seed(session: AsyncSession) -> None:
    print("Deleting existing DemoClient + ClientPortfolioHolding records...")
    await session.execute(delete(ClientPortfolioHolding))
    await session.execute(delete(DemoClient))
    await session.flush()

    print(f"Inserting {len(CLIENTS)} clients with their holdings...")
    for i, client_data in enumerate(CLIENTS, 1):
        holdings_data = client_data.pop("holdings")
        client = DemoClient(**client_data, tag="capcodemo")
        session.add(client)
        await session.flush()  # get the UUID

        for h in holdings_data:
            holding = ClientPortfolioHolding(
                client_id=client.id,
                as_of_date=AS_OF,
                **h,
            )
            session.add(holding)

        print(f"  [{i}/{len(CLIENTS)}] {client.firstname} {client.lastname} — {len(holdings_data)} holdings")

    await session.commit()
    print("Done.")


async def main() -> None:
    if not settings.database_configured:
        raise RuntimeError("DATABASE_URL not configured")

    engine = create_async_engine(_async_url(settings.DATABASE_URL), echo=False, future=True)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    async with session_maker() as session:
        await seed(session)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
