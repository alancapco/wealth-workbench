"""AAOIFI knowledge base ingest script.

Adapted from islamic-ai/shariah scripts/ingest_ss8_draft.py for RM Workbench.
Ingests AAOIFI Shariah standards PDF at page granularity (covers all 54 standards).
Status written as 'draft' — administrator + qualified scholar must approve before RAG queries use them.

Usage:
    cd backend && uv run python -m app.scripts.ingest_aaoifi
    cd backend && uv run python -m app.scripts.ingest_aaoifi --pdf /path/to/Shariaa-Standards-ENG.pdf
    cd backend && uv run python -m app.scripts.ingest_aaoifi --dsn postgresql://user:pw@host/db

Do NOT run during tests or application startup.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import os
import re
import sys
from pathlib import Path
from uuid import UUID, uuid5

import asyncpg

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber is required. Run: uv add pdfplumber", file=sys.stderr)
    sys.exit(1)

NAMESPACE = UUID('c6ca3d31-23c1-4d8c-9e77-f2d0fa10e8dd')

# Standard detection: "Shari'ah Standard No. (N): Title"
STANDARD_HEADER_RE = re.compile(
    r"Shari.ah Standard No\.\s*\((\d+)\)\s*[:\-]?\s*(.+)", re.IGNORECASE
)
# Clause detection: N/N or N/N/N followed by text
CLAUSE_RE = re.compile(r'^\s*(?P<id>\d+/\d+(?:/\d+)?)\s+(?P<text>.+)$')
PAGE_FOOTER_RE = re.compile(r'^\s*\d{2,6}\s*$')


def _stable_id(key: str) -> UUID:
    return uuid5(NAMESPACE, key)


def _collapse(value: str) -> str:
    return re.sub(r'\s+', ' ', value).strip()


def _clean_lines(raw: str) -> list[str]:
    result = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or PAGE_FOOTER_RE.fullmatch(line):
            continue
        result.append(line)
    return result


def _parse_pages(pdf_path: Path) -> list[dict]:
    """
    Page-granularity parse: one clause record per PDF page.
    Detects standard boundaries by header pattern.
    Returns list of dicts: {standard_number, standard_title, page_num, text}
    """
    pages_data = []
    current_standard: tuple[str, str] | None = None  # (number, title)

    with pdfplumber.open(str(pdf_path)) as pdf:
        total = len(pdf.pages)
        print(f"PDF has {total} pages — scanning for standard boundaries...")

        for page_num, page in enumerate(pdf.pages, start=1):
            try:
                raw = page.dedupe_chars(tolerance=1).extract_text(x_tolerance=2, y_tolerance=3) or ''
            except Exception:
                raw = page.extract_text() or ''

            lines = _clean_lines(raw)
            full_text = _collapse(' '.join(lines))

            # Detect new standard boundary
            for line in lines[:10]:  # Header appears near top of page
                m = STANDARD_HEADER_RE.search(line)
                if m:
                    current_standard = (m.group(1).strip(), _collapse(m.group(2)))
                    break

            if current_standard is None or len(full_text) < 40:
                continue

            pages_data.append({
                'standard_number': current_standard[0],
                'standard_title': current_standard[1],
                'page_num': page_num,
                'text': full_text,
            })

            if page_num % 50 == 0:
                print(f"  Scanned page {page_num} / {total}...")

    return pages_data


async def ingest(pdf_path: Path, dsn: str, replace: bool) -> None:
    if not pdf_path.exists():
        print(f"ERROR: PDF not found at {pdf_path}", file=sys.stderr)
        sys.exit(1)

    source_hash = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    print(f"Source PDF: {pdf_path.name} (SHA-256: {source_hash[:16]}...)")

    pages_data = _parse_pages(pdf_path)

    # Group by standard
    standards: dict[str, dict] = {}
    clauses_by_standard: dict[str, list[dict]] = {}
    for page in pages_data:
        snum = page['standard_number']
        if snum not in standards:
            standards[snum] = {
                'standard_number': snum,
                'title': page['standard_title'],
            }
            clauses_by_standard[snum] = []
        clauses_by_standard[snum].append(page)

    print(f"Found {len(standards)} standards across {len(pages_data)} content pages.")

    conn = await asyncpg.connect(dsn)
    try:
        total_clauses = 0
        async with conn.transaction():
            for snum, std_info in standards.items():
                standard_id = _stable_id(f'aaoifi:{snum}:{source_hash}:draft-standard')

                if replace:
                    await conn.execute(
                        'DELETE FROM aaoifi_clauses WHERE standard_id = $1',
                        standard_id,
                    )
                    await conn.execute(
                        'DELETE FROM aaoifi_standards WHERE id = $1',
                        standard_id,
                    )

                await conn.execute(
                    '''INSERT INTO aaoifi_standards
                         (id, authority, standard_number, title, edition,
                          source_checksum, approval_status, language)
                       VALUES ($1, 'AAOIFI', $2, $3, 'Shari''ah Standards', $4, 'draft', 'en')
                       ON CONFLICT (authority, standard_number, edition, language, source_checksum)
                       DO NOTHING''',
                    standard_id,
                    snum,
                    std_info['title'],
                    source_hash,
                )

                for page_record in clauses_by_standard[snum]:
                    page_num = page_record['page_num']
                    text = page_record['text']
                    clause_id = f"page:{page_num}"
                    clause_db_id = _stable_id(f'aaoifi:{snum}:{source_hash}:clause:{clause_id}')

                    await conn.execute(
                        '''INSERT INTO aaoifi_clauses
                             (id, standard_id, clause_id, parent_clause_id, breadcrumb,
                              verbatim_text, embedding_text,
                              source_pdf_page_start, source_pdf_page_end,
                              printed_page_start, printed_page_end,
                              language, approval_status)
                           VALUES ($1, $2, $3, NULL, $4, $5, $5, $6, $6, $6, $6, 'en', 'draft')
                           ON CONFLICT (standard_id, clause_id) DO UPDATE SET
                             verbatim_text    = EXCLUDED.verbatim_text,
                             embedding_text   = EXCLUDED.embedding_text,
                             approval_status  = 'draft' ''',
                        clause_db_id,
                        standard_id,
                        clause_id,
                        f"SS {snum} > Page {page_num}",
                        text,
                        page_num,
                    )
                    total_clauses += 1

                print(f"  Ingested SS {snum}: {std_info['title']!r} ({len(clauses_by_standard[snum])} pages)")

        print(f"\nDone. Ingested {len(standards)} standards, {total_clauses} page records.")
        print("Status: draft only. Run approval workflow before RAG queries will use these clauses.")

    finally:
        await conn.close()


def _resolve_pdf_path() -> Path:
    # 1. Explicit env var
    env_path = os.getenv('AAOIFI_PDF_PATH', '')
    if env_path:
        return Path(env_path)

    # 2. SHARIAH_TOOLS_PATH/data/Shariaa-Standards-ENG.pdf
    tools_path = os.getenv('SHARIAH_TOOLS_PATH', '')
    if tools_path:
        candidate = Path(tools_path) / 'data' / 'Shariaa-Standards-ENG.pdf'
        if candidate.exists():
            return candidate

    # 3. Fallback relative to project root
    return Path('/data/Shariaa-Standards-ENG.pdf')


def main() -> None:
    # Import settings here so this file can also be run before app boot
    try:
        from app.core.config import settings as app_settings
        default_dsn = (app_settings.DATABASE_URL or '').replace('postgresql+asyncpg://', 'postgresql://')
    except Exception:
        default_dsn = ''

    parser = argparse.ArgumentParser(description='Ingest AAOIFI Shariah standards PDF into the knowledge base.')
    parser.add_argument('--pdf', type=str, help='Path to Shariaa-Standards-ENG.pdf (overrides env vars)')
    parser.add_argument('--dsn', type=str, default=default_dsn, help='PostgreSQL DSN (defaults to DATABASE_URL)')
    parser.add_argument('--replace', action='store_true', help='Delete existing records for same standard before reinserting')
    args = parser.parse_args()

    pdf_path = Path(args.pdf) if args.pdf else _resolve_pdf_path()
    if not args.dsn:
        print("ERROR: --dsn required (or set DATABASE_URL env var)", file=sys.stderr)
        sys.exit(1)

    asyncio.run(ingest(pdf_path, args.dsn, args.replace))


if __name__ == '__main__':
    main()
