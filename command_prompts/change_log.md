## PlanCast Change Log — Frontend Conversion/WebSocket/CORS/DB Fixes

Date: 2025-08-18

### Backend API (FastAPI)
- Mounted generated models for direct download/preview:
  - Added static mount `app.mount("/models", StaticFiles(directory="output/generated_models"))` in `api/main.py`.
- Public URL support for absolute asset links:
  - Added `PUBLIC_API_URL` env usage to prefix `/models/...` links when present.
- Processing result payloads:
  - `process_floorplan_background` now assembles `result_data` with `model_url`, `formats`, and a per-format `output_files` map using `/models/{job_id}/...`.
  - `GET /jobs/{job_id}/status` now returns a `result` object with the same fields for the frontend preview and downloads.
- Error handling and CORS:
  - Introduced `ErrorResponse` model.
  - Ensured error handlers attach `Access-Control-Allow-Origin`, `Access-Control-Allow-Credentials`, and `Access-Control-Expose-Headers` so browsers receive readable JSON on failures.
  - `/convert` and `/jobs/{id}/status` now return JSON error bodies with CORS headers to aid debugging.
- Job creation and admin provisioning:
  - Initially auto-provisioned `admin@plancast.com` if missing; then switched to raw SQL to insert/select admin with correct enum casing to avoid ORM/enum mismatches.
  - Captured `project_id` before closing the DB session in `/convert` to prevent SQLAlchemy detached instance refresh errors when scheduling background tasks and building responses.
  - Fixed `/jobs/{job_id}/status` to accept `request`, sanitize `job_id` (handles encodings like `%7B6%7D`), and use the correct `project.output_files` field. Returns consistent JSON with CORS headers on errors.

### WebSocket (Socket.IO)
- Server configuration (`services/websocket_manager.py`):
  - Forced `async_mode='asgi'` and set explicit `socketio_path='socket.io'` for Railway compatibility.
  - Built result payloads using `project.output_files` and `PUBLIC_API_URL` for model URLs in real-time updates.
- ASGI mounting / Process startup:
  - `Procfile` updated to run `uvicorn api.main:socketio_app` (previously `api.main:app`) so the Socket.IO ASGI app serves connections in production.

### Database/ORM Alignment
- Enum bindings (`models/database.py`):
  - Bound SQLAlchemy enums to existing Postgres types via `Enum(..., values_callable=..., name=...)`.
  - `SubscriptionTier` now matches DB enum values exactly (`free`/`pro`/`enterprise`), and inserts use lowercase.
  - `ProjectStatus` uses lowercase values (pending/processing/completed/failed/cancelled) matching DB enum.
  - `UsageLog.action_type` bound to `actiontype` enum.
- Project schema parity with migration:
  - Removed non-existent columns (e.g., `scale_reference`, `warnings`, `started_at`, `building_dimensions`, `output_files_json`).
  - Added/renamed fields to match DB: `output_files` JSON; `updated_at` present.
  - Set `updated_at` `server_default=NOW()` and `onupdate=NOW()` to satisfy NOT NULL constraint.
- Repository changes (`models/repository.py`):
  - `create_project` no longer passes removed fields; explicitly sets `updated_at` on insert for safety.
  - `log_usage` now writes `processing_time_seconds` and removed non-existent columns (`credits_used`, `ip_address`, `user_agent`) to match DB.

### Conversion Endpoint Flow (`/convert`)
- Validates upload via `PlanCastValidator` and creates a DB project using the aligned schema.
- Starts background processing; later steps broadcast via WebSocket and write exported file links under `/models/{job_id}/...`.
- All error responses now include detailed messages and CORS headers for browser visibility.

### Frontend
- WebSocket client (`plancast-frontend/hooks/useWebSocket.ts`):
  - Set `path: '/socket.io'`, enabled `withCredentials`, and prefer `polling` first to tolerate Railway proxies; keeps `upgrade` to websocket when available.
- WebSocket provider (`lib/websocket-context.tsx`):
  - Enabled `autoConnect: true` so unauthenticated users still receive job updates.
- Job status hook (`hooks/useJobStatus.ts`):
  - Fetches from `NEXT_PUBLIC_API_URL`, parses `progress_percent`, and normalizes timestamps.
- Preview page (`app/convert/preview/[jobId]/page.tsx`):
  - Removed `any` usage; introduced `JobResult` type.
  - Uses `result.output_files[format]` when available; falls back to `result.model_url`.
  - Formats list trimmed to supported defaults when server does not specify.

### Deployment / Config
- Environment variables to set:
  - Railway (backend): `PUBLIC_API_URL=https://api.getplancast.com`.
  - Vercel (frontend): `NEXT_PUBLIC_API_URL=https://api.getplancast.com`, `NEXT_PUBLIC_WS_URL=wss://api.getplancast.com` (set for Production and Preview).
- `Procfile` changed to serve the Socket.IO ASGI app.

### Notable Bug Fixes (chronological)
- WebSocket failures (500 on handshake) → run ASGI app, configure path and async mode.
- CORS blocks and opaque 500s → error handlers emit CORS headers and JSON bodies.
- DB enum mismatches:
  - `subscriptiontier` casing → uppercase enums and raw SQL admin bootstrap.
  - `projectstatus` casing → lowercase enums and bound SQLAlchemy Enum.
- Schema mismatches:
  - Removed `scale_reference` from project insert; matched ORM to migration.
  - `updated_at` NOT NULL violation → server default + explicit set on insert.

### Outcome
- Frontend now connects via WebSocket and should receive job updates.
- `/convert` requests create projects with correct schema/enums; errors surface with readable JSON.
- Generated models are served under `/models/{job_id}/...` for preview and download.


