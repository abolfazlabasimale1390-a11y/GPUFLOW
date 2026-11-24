# GPUFlow Local Lab — Architecture Notes

## Purpose

Validate the first user-facing workflow and local device communication before integrating real inference providers. This build is a prototype, not a production GPU scheduler.

## Runtime flow

1. A browser submits the access password to `POST /api/unlock`.
2. The server creates a short-lived in-memory token.
3. The browser opens `WS /ws` with token, room and display name.
4. The server tracks connected sockets by room and broadcasts presence, chat, and route-simulation events.
5. The route demo applies a small deterministic heuristic and broadcasts the result.

## Current constraints

- In-memory state only; restart clears rooms and tokens.
- No real LLM/provider integrations or GPU execution.
- No durable storage, distributed coordination, TLS termination, or production identity system.
- Run only on a trusted local network.

## Suggested production direction

Introduce provider adapters behind a stable interface, policy-based routing with explicit quality/cost/latency constraints, PostgreSQL persistence, Redis-backed coordination, structured telemetry, real authentication, TLS, rate limiting, request redaction, and reproducible evaluations. Do not claim savings until benchmark data supports it.
