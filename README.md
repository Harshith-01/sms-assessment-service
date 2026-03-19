Initialize Assessment

## Overview

`assessment-service` manages exam and assignment lifecycles, marks entry and verification, grade scales, and student historical results.

Base URL (local): `http://127.0.0.1:8005`

API root prefix: `/assessment`

Health endpoint: `/health`

## Core Capabilities

- Grade scale and grade band management
- Component weight configuration
- Exam creation, publication, cancellation
- Exam-subject linking
- Student exam registration and bulk marks upload
- Assignment creation, publication, submission, and marking
- Assignment mark verification
- Report card generation and publication
- Student exam/academic/assignment history retrieval
- Student progress summary endpoint
- Partial-success bulk processing with row-level error reporting

## Security Model

- JWT Bearer token authentication
- Role-based authorization with guarded endpoints
- Supported roles in routes: `ADMIN`, `TEACHER`, `STUDENT`, `PARENT`, `SERVICE`
- Request rate limiting via `slowapi`
- Trusted host filtering and CORS controls
- Security headers middleware enabled
- Request body size limit: `5 MB`

## API Groups

All endpoints are under `/assessment`.

- `POST /grade-scales`, `GET /grade-scales`, `PUT /grade-scales/{scale_id}`, `DELETE /grade-scales/{scale_id}`
- `POST /grade-bands`, `GET /grade-bands`
- `POST /component-weights`, `GET /component-weights`
- `POST /exams`, `GET /exams`, `GET /exams/{exam_id}`, `PUT /exams/{exam_id}`, `PATCH /exams/{exam_id}/publish`, `PATCH /exams/{exam_id}/cancel`
- `POST /exam-subjects`, `GET /exam-subjects`
- `POST /exam/register-students`
- `POST /marks/bulk`, `PATCH /marks/{registration_id}/verify`
- `POST /assignments`, `GET /assignments`, `GET /assignments/{assignment_id}`, `PUT /assignments/{assignment_id}`
- `PATCH /assignments/{assignment_id}/publish`, `PATCH /assignments/{assignment_id}/close`, `PATCH /assignments/{assignment_id}/cancel`
- `POST /assignments/{assignment_id}/submit`
- `POST /assignments/marks/bulk`, `PATCH /assignment-marks/{submission_id}/verify`
- `POST /report-cards/generate`, `POST /report-cards/publish`, `GET /report-cards/student/{student_id}`
- `GET /history/student/{student_id}/exam`
- `GET /history/student/{student_id}/academic`
- `GET /history/student/{student_id}/assignments`
- `GET /progress/student/{student_id}`

## Behavior Updates (2026)

- `POST /assessment/exam/register-students` now runs in partial-commit mode.
	- Returns `created`, `processed`, `skipped`, and `errors` so valid rows are committed while invalid rows are reported.
- Bulk operation responses are now standardized with optional metadata fields:
	- `processed`, `skipped`, `errors` (in addition to `message`, `count`).
- Progress endpoint (`GET /assessment/progress/student/{student_id}`) aggregates assignment and exam trends for dashboard use.
	- Parent role access is enabled for holistic student progress visibility in parent-facing dashboards.

## Environment Variables

Use `.env` in this service directory.

- `DATABASE_URL` (required)
- `JWT_SECRET_KEY` or `SECRET_KEY` (one is required)
- `ACCESS_TOKEN_EXPIRE_MINUTES` (default: `60`)
- `ALLOWED_ORIGINS` (comma-separated)
- `ALLOWED_HOSTS` (comma-separated)
- `SERVICE_NAME` (default: `assessment-service`)
- `INTERNAL_SERVICE_TOKEN`
- `INTERNAL_SERVICE_NAME`
- `INTERNAL_ALLOWED_SERVICES`

Reference file: `.env.example`

## Local Development

### 1) Install dependencies

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

### 2) Configure environment

```bash
cp .env.example .env
```

Set valid DB and secrets in `.env`.

### 3) Run service

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The service is typically exposed as `8005` from compose (`8005:8000`).

## Docker

Build and run locally:

```bash
docker build -t assessment-service:local .
docker run --rm -p 8005:8000 --env-file .env assessment-service:local
```

Production compose file: `docker-compose.prod.yml`

## Deployment

Deployment helper script: `ops/deploy.sh`

Expected behavior:

- Checks out deployment branch
- Pulls latest code
- Pulls image (best effort)
- Starts/updates service via compose
- Prunes dangling images

## Testing

Test file: `tests/test_assessment_api.py`

Run:

```bash
pytest -q
```

## Operational Notes

- OpenAPI docs are available at `/docs` unless disabled by host policy.
- Health check response format:

```json
{"service":"assessment-service","status":"ok"}
```

- Ensure all dependent services share the same JWT secret and internal token policy.

## Production Readiness Checklist

- Set strong secrets (`JWT_SECRET_KEY`/`SECRET_KEY`, internal service token)
- Restrict `ALLOWED_HOSTS` and `ALLOWED_ORIGINS`
- Use managed PostgreSQL with backups enabled
- Run service behind reverse proxy/TLS ingress
- Configure centralized logs and alerting
- Execute full integration tests before release
