"""
Shariah RAG service — AAOIFI clause retrieval using hybrid search.
Adapted from islamic-ai/shariah search_repository.py for standard PostgreSQL
(replaces ParadeDB BM25 with tsvector/tsquery + ts_rank).
"""
from __future__ import annotations

import asyncio
import re
from collections import defaultdict
from typing import Any, TypedDict

import asyncpg

_STOP_WORDS = frozenset({
    'about', 'after', 'against', 'also', 'among', 'and', 'any', 'are', 'as', 'at', 'be',
    'been', 'between', 'by', 'can', 'contract', 'customer', 'for', 'from', 'has', 'have',
    'in', 'into', 'is', 'it', 'its', 'of', 'on', 'or', 'shall', 'that', 'the', 'their',
    'this', 'to', 'under', 'which', 'with', 'will', 'would',
})

CITATION_PATTERN = re.compile(r'(?i)\b(?:ss|standard)\s*([0-9]+)\s*(?:·|/)\s*([0-9]+(?:/[0-9]+)?)\b')

BASE_FIELDS = """
  c.id AS clause_db_id,
  s.authority,
  s.standard_number,
  s.title,
  c.clause_id,
  c.verbatim_text,
  c.printed_page_start,
  c.printed_page_end,
  c.source_pdf_page_start,
  c.source_pdf_page_end
"""

# Standard PostgreSQL tsvector/tsquery sparse search — replaces ParadeDB BM25
SPARSE_SQL = f"""
SELECT {BASE_FIELDS}
FROM aaoifi_clauses c
JOIN aaoifi_standards s ON s.id = c.standard_id
WHERE to_tsvector('english', c.embedding_text) @@ plainto_tsquery('english', $1)
  AND c.approval_status = 'approved'
  AND s.approval_status = 'approved'
  AND s.authority = $2
  AND ($3::text IS NULL OR s.standard_number = $3)
  AND c.language = $4
ORDER BY ts_rank(to_tsvector('english', c.embedding_text), plainto_tsquery('english', $1)) DESC,
         c.id
LIMIT $5
"""

# pgvector dense (ANN) search
DENSE_SQL = f"""
SELECT {BASE_FIELDS}
FROM aaoifi_clauses c
JOIN aaoifi_standards s ON s.id = c.standard_id
WHERE c.embedding IS NOT NULL
  AND c.approval_status = 'approved'
  AND s.approval_status = 'approved'
  AND s.authority = $2
  AND ($3::text IS NULL OR s.standard_number = $3)
  AND c.language = $4
ORDER BY c.embedding <=> $1::vector,
         c.id
LIMIT $5
"""

# Direct citation lookup — e.g. "SS 8 / 4/6"
DIRECT_SQL = f"""
SELECT {BASE_FIELDS}
FROM aaoifi_clauses c
JOIN aaoifi_standards s ON s.id = c.standard_id
WHERE s.standard_number = $1
  AND c.clause_id = $2
  AND c.approval_status = 'approved'
  AND s.approval_status = 'approved'
  AND s.authority = $3
  AND c.language = $4
LIMIT 1
"""

COUNT_APPROVED_SQL = """
SELECT COUNT(*) FROM aaoifi_clauses WHERE approval_status = 'approved'
"""


class ShariahClauseResult(TypedDict):
    clause_db_id: str
    citation: dict[str, Any]
    excerpt: str
    fused_score: float


def _citation_terms(query: str) -> tuple[str, str] | None:
    match = CITATION_PATTERN.search(query)
    return (match.group(1), match.group(2)) if match else None


def _extract_keywords(text: str, limit: int = 30) -> str:
    """Extract keywords for sparse search by filtering stop words."""
    words = re.findall(r"[A-Za-z][A-Za-z''-]{2,}", text.lower())
    selected: list[str] = []
    seen: set[str] = set()
    for word in words:
        if word in _STOP_WORDS or word in seen:
            continue
        seen.add(word)
        selected.append(word)
        if len(selected) == limit:
            break
    return ' '.join(selected) or 'investment review'


def _row_to_candidate(row: asyncpg.Record) -> dict[str, Any]:
    return {
        'clause_db_id': str(row['clause_db_id']),
        'citation': {
            'authority': row['authority'],
            'standard_number': row['standard_number'],
            'title': row['title'],
            'clause_id': row['clause_id'],
            'page': row['printed_page_start'],
            'printed_page_start': row['printed_page_start'],
            'printed_page_end': row['printed_page_end'],
        },
        'excerpt': row['verbatim_text'][:700],
    }


class ShariahRagService:
    """
    3-way hybrid AAOIFI clause search for WM Workbench.

    Search branches:
      - sparse:  PostgreSQL tsvector/tsquery + ts_rank (was ParadeDB BM25)
      - dense:   pgvector cosine similarity (when embedding provided)
      - direct:  exact citation lookup (SS N / clause_id pattern)

    Scores fused with Reciprocal Rank Fusion (RRF, k=60).
    """

    def __init__(self, db_url: str) -> None:
        self._db_url = db_url
        self._pool: asyncpg.Pool | None = None

    async def _get_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            # Strip SQLAlchemy driver prefix for asyncpg
            dsn = self._db_url.replace("postgresql+asyncpg://", "postgresql://")
            self._pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5)
        return self._pool

    async def _fetch(self, sql: str, *params: Any) -> list[asyncpg.Record]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            return await conn.fetch(sql, *params)

    async def search(
        self,
        query: str,
        authority: str = "AAOIFI",
        standard_number: str | None = None,
        language: str = "en",
        limit: int = 8,
        query_embedding: list[float] | None = None,
    ) -> list[ShariahClauseResult]:
        """
        Hybrid search: sparse + optional dense + optional direct citation.
        Returns results fused with RRF, sorted by descending fused_score.
        """
        citation = _citation_terms(query)
        pending = [
            self._fetch(SPARSE_SQL, query, authority, standard_number, language, limit),
        ]
        branch_names = ['sparse']

        if query_embedding is not None:
            vector_literal = '[' + ','.join(str(v) for v in query_embedding) + ']'
            pending.append(self._fetch(
                DENSE_SQL,
                vector_literal,
                authority,
                standard_number,
                language,
                limit,
            ))
            branch_names.append('dense')

        if citation is not None:
            pending.append(self._fetch(
                DIRECT_SQL,
                citation[0],
                citation[1],
                authority,
                language,
            ))
            branch_names.append('direct')

        branch_rows = await asyncio.gather(*pending)

        candidates: dict[str, dict[str, Any]] = {}
        ranks: dict[str, dict[str, int]] = defaultdict(dict)

        for branch, rows in zip(branch_names, branch_rows, strict=True):
            for position, row in enumerate(rows, start=1):
                cid = str(row['clause_db_id'])
                candidates[cid] = _row_to_candidate(row)
                ranks[cid][branch] = position

        results = []
        for cid, candidate in candidates.items():
            branch_ranks = ranks[cid]
            # RRF with k=60; direct citation gets a +1.0 bonus
            fused_score = sum(1.0 / (60 + rank) for rank in branch_ranks.values())
            if 'direct' in branch_ranks:
                fused_score += 1.0
            results.append({**candidate, 'fused_score': fused_score})

        results.sort(key=lambda r: (-r['fused_score'], r['clause_db_id']))
        return results[:limit]  # type: ignore[return-value]

    async def get_candidate_sources(
        self,
        text: str,
        limit: int = 8,
        authority: str = "AAOIFI",
        language: str = "en",
    ) -> list[dict[str, Any]]:
        """
        Extract keywords from text and run sparse search.
        Returns formatted citation list suitable for LLM context.
        """
        keyword_query = _extract_keywords(text, limit=30)
        rows = await self._fetch(SPARSE_SQL, keyword_query, authority, None, language, limit)
        sources = []
        for row in rows:
            s = row['standard_number']
            cid = row['clause_id']
            sources.append({
                'source_key': f"SS {s} {cid}",
                'standard_number': s,
                'title': row['title'],
                'clause_id': cid,
                'printed_page_start': row['printed_page_start'],
                'verbatim_text': row['verbatim_text'],
            })
        return sources

    async def has_approved_clauses(self) -> bool:
        """Return True if at least one approved clause exists (used by evidence_service)."""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                count = await conn.fetchval(COUNT_APPROVED_SQL)
            return (count or 0) > 0
        except Exception:
            return False

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
