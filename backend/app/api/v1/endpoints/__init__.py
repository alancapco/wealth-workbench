"""API v1 endpoint modules.

Route prefixes are intentionally doubled for four routers mounted in
``app/api/v1/__init__.py`` (e.g. ``/api/v1/calendar/calendar/events``,
``/api/v1/artifacts/artifacts/{id}``, ``/api/v1/telemetry/telemetry/events``,
``/api/v1/meetings/meetings/{id}``). ``frontend/lib/endpoints.ts`` matches these
paths, so do not "fix" the prefixes without changing both sides together.
"""
