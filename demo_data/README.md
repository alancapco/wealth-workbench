# SYNTHETIC DEMO DATA — RM Workbench MVP · Demo Seed Pack v1.3

> **SYNTHETIC DEMO DATA · 100% synthetic · DESIGN ONLY.** Every name, identifier,
> email address, issuer, price and document in this directory is fabricated. No real
> person, client, issuer, bank, vendor, religious ruling, credential, phone number
> or email address is present. All email addresses use the reserved fake domain
> `@demo.invalid`; all instrument symbols use the `SYN-` prefix.

**Generator / seed registry (binding):** one numeric seed `20261105`; generator id
`RM-WB-DEMO-v1.3`; `splitmix64` namespaced sub-seeds; `world_as_of`
`2026-11-05T17:00:00+08:00` (prior close, SGT); demo clock live tick
`2026-11-06 09:58:14 SGT`; single Approve `10:14:32 SGT`; base SGD / Singapore /
SGT / English with minority HKD and USD. Market source is the versioned placeholder
`<source>` (OD-7/8) — **no vendor is ever named**.

## What this directory IS

These files are the **SPECIFIED OUTPUT SHAPE of a future generator** — a static,
labelled preview of the seeded world that a future `H2` generator will emit in
`seed` / `replay` / `live` mode. They are **DATA**, not a running generator, not
application code, not a scaffold, not executed DDL and not a production migration.
No generator, script or executable is included here.

## Honesty posture (frozen taxonomy + E-10 qualifier)

| Posture | What it covers in this pack |
|---|---|
| **REAL** | the live tick `tk_live_0001` (wall-clock `as_of 09:58:14 SGT`), the C-1 chips, the approval gate |
| **REAL (SANDBOXED)** | HubSpot Free demo sandbox portal — real vendor service, 100% synthetic records, 0 real persons contacted |
| **SIMULATED** | seeded world; replay ticks; Retell simulation/test call with a synthetic caller; scripted transcript |
| **STUBBED** | `local_stub` / `scripted_stub` / `demo_sink` bindings; CRM adapter local projection; email demo sink |
| **EXTERNAL** | Shariah project — preference-flag pointer only, flag OFF |
| **HARD-BLOCKED** | trade execution — **no trade/order table, no execution path** |

**Three zero counters:** `0 real dialled calls` · `0 real client-facing sends` · `0 real PII`.
Together with the frozen `0 sends` / `0 trades`, see `demo_sink_messages.csv` and
`integrity_report.json`. A post-Approve write to the sandbox portal is permitted and
is explicitly **not** a send.

## Column conventions

Every CSV row begins with the same eight columns (the full C-1 envelope plus the
synthetic marker): `synthetic_marker, source_id, source_kind, as_of, ingested_at,
confidence, mode, version_stamp`. All seven C-1 columns are **non-null on every fact
row**. `ingested_at` is a fixed generation wall-clock and is excluded from checksums.
Every JSON file carries a top-level `"synthetic_marker": "SYNTHETIC DEMO DATA"`.
No CSV contains comment lines — all files are machine-parseable.

`clients.csv` carries BOTH the projector-visible text registry key `client_id`
(`cl_wong_001`, used by every flat-file FK) and `client_id_uuid` — a deterministic
RFC-4122 v4 UUID derived from `splitmix64(20261105, '<client_id>')`.
`crm_contacts.csv` carries the same `client_id_uuid` so the physical DEFERRABLE FK
`crm.crm_contact.client_id_uuid → client.client(client_id)` is 1:1 (12_… §4.10
deviation 1). No literal text→uuid FK is emitted.

## Idempotency (12_… §4.10 deviation 2)

The literal registry rule is `approval_token + field_mapping_version` (stored as
text in `crm_field_mapping.csv`). The physical key appends `mapping_id` so the six
accepted writes do not collapse into one UNIQUE key: e.g.
`appr_001:fmv_20261105_1:map_01`. `crm_sync_log.csv` carries six distinct keys for
`map_01…map_06` plus unique keys for the pending/failed rows.

## Volume note (demo-scale, E-6 / NFR-9)

`market_ticks_replay.csv` is a **representative 120-frame excerpt**. The full ~1,200-frame
recorded stream is generator-emitted and is **not padded to a fake 1,200** here; the
manifest records `row_count: 120` and `full_stream_row_count: 1200`. The whole pack
resets in ≤60s.

## Integrity

`checksums.sha256` holds REAL SHA-256 hashes of the 51 emitted data files PLUS a
52nd control-file verification line for `manifest_addendum_crm.json` (leading `#`
banner line is a comment; verify with `grep -v '^#' checksums.sha256 | shasum -a 256 -c -`).
`dataset_checksum` = SHA-256 of the concatenation of the 51 per-file data hashes,
sorted by filename (the 52nd addendum line is a control verification line excluded
from `dataset_checksum` to avoid self-reference). `manifest_v1.3.json` is
**READ-ONLY and MUST NOT be bumped**; the 52nd file is declared in the ADDENDUM
itself, in `checksums.sha256`, `integrity_report.json` and `13_Demo_Seed_Pack.md`.
See `integrity_report.json` for the PASS checks.

## External vendor adapters (E-9…E-14) / manifest_addendum_crm.json

HubSpot Free (primary external CRM) and Retell AI (optional voice agent) are
**EXTERNAL REFERENCES**. No new Postgres table was added; the six `crm.*` tables
are re-purposed as `CRM ADAPTER · LOCAL PROJECTION`. The additive `crm.*` tables and
vendor external-reference files are declared in the separate architect-authored
`manifest_addendum_crm.json` (Phase-4 sync), **NOT inside `manifest_v1.3.json`**.
See `14_Vendor_Adapter_Ruling_HubSpot_Retell.md` (authoritative) and
`13_Demo_Seed_Pack.md` §External vendor adapters. Retell's native HubSpot
integration is **OFF**; the token is the literal placeholder
`<HUBSPOT_PRIVATE_APP_TOKEN>` and lives out of band (DI-19).

