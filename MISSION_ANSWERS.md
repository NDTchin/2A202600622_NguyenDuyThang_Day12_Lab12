# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found

1. Hardcoded configuration such as host, port, API keys, and debug settings.
2. Secrets can be committed accidentally when they are stored directly in code.
3. No health check or readiness endpoint for cloud platforms and load balancers.
4. No graceful shutdown handling for SIGTERM during deploys or restarts.
5. Using local-only assumptions such as in-memory state and fixed ports.
6. Unstructured `print()` logging, which is hard to search in cloud logs.
7. No authentication, rate limiting, or cost guard for a public API.

### Exercise 1.2: Basic version run result

The basic app can run locally and answer `/ask`, but it is not production-ready because it depends on local assumptions and lacks security, health checks, and externalized configuration.

### Exercise 1.3: Comparison table

| Feature | Develop | Production | Why Important? |
|---|---|---|---|
| Config | Hardcoded/default local values | Environment variables | Same code can run in local, staging, and cloud without edits. |
| Secrets | Risk of being stored in code | Loaded from env/platform secrets | Prevents leaking keys in Git history. |
| Port | Fixed local port | Uses `PORT` from platform | Cloud platforms assign runtime ports dynamically. |
| Health | Missing or minimal | `/health` and `/ready` | Enables restart, routing, monitoring, and zero-downtime deploys. |
| Logging | Plain print/debug logs | Structured JSON logs | Easier to filter, search, and alert in production. |
| Shutdown | Abrupt process stop | SIGTERM/graceful shutdown | Allows in-flight requests to finish during deploys. |
| State | In-memory | Redis-backed | Supports multiple instances and survives restarts. |

## Part 2: Docker

### Exercise 2.1: Dockerfile questions

1. Base image: `python:3.11-slim`, which provides Python with a smaller Debian-based runtime.
2. Working directory: `/app` for runtime code and `/build` for dependency installation in the builder stage.
3. Copying `requirements.txt` before source code improves Docker layer caching.
4. `CMD` provides the default command and can be overridden. `ENTRYPOINT` is harder to override and is usually for fixed executables.

### Exercise 2.2: Build and run

The final app is intended to run with:

```bash
cd 06-lab-complete
docker compose up --build
curl http://localhost:8000/health
```

### Exercise 2.3: Image size comparison

- Develop image: expected to be larger because dependencies and build tools stay in the same layer.
- Production image: expected to be smaller because it uses a multi-stage build and `python:3.11-slim`.
- Difference: target is under 500 MB for the final image.

### Exercise 2.4: Docker Compose stack

```text
Client -> Nginx (host port 8080, container port 80) -> Agent/FastAPI (port 8000) -> Redis
```

The final `docker-compose.yml` defines `nginx`, `agent`, and `redis` services with health checks.

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment

- URL: TODO after deployment
- Config: `06-lab-complete/railway.toml`
- Required variables: `AGENT_API_KEY`, `JWT_SECRET`, `REDIS_URL`, `PORT`, `RATE_LIMIT_PER_MINUTE`, `MONTHLY_BUDGET_USD`
- Application payload: Day 10 cleaned paper corpus and observability metrics are packaged in `06-lab-complete/day10_artifacts`.

### Exercise 3.2: Render deployment

- Config: `06-lab-complete/render.yaml`
- Render can deploy the Docker service and generate secret values for `AGENT_API_KEY` and `JWT_SECRET`.

### Exercise 3.3: GCP Cloud Run

Cloud Run is a good fit for stateless containers because it routes traffic to containers, injects environment variables, and supports health checks and autoscaling.

## Part 4: API Security

### Exercise 4.1: API key authentication

The final app requires `X-API-Key` on protected endpoints. Missing or invalid keys return `401`.

Local verification:

```text
POST /ask without X-API-Key -> 401
POST /ask with X-API-Key: local-dev-key -> 200
```

### Exercise 4.2: JWT authentication

JWT is useful when the service needs user identity, roles, and token expiration without storing login sessions on the API server. The final submission uses API key authentication because the checklist requires it.

### Exercise 4.3: Rate limiting

The final app limits each `user_id` to `10 req/min` by default. The implementation stores the sliding window in Redis when `REDIS_URL` is configured.

Local verification:

```text
12 requests for one user_id -> ok=10 limited=2 other=0
```

### Exercise 4.4: Cost guard implementation

The final app estimates input/output tokens and records per-user monthly cost. If a user reaches the configured `MONTHLY_BUDGET_USD` (default `$10`), `/ask` returns `402`.

The usage records are keyed by `user_id` and month, so the guard works across multiple app instances when Redis is enabled.

## Part 5: Scaling & Reliability

### Exercise 5.1: Health checks

- `/health`: liveness check, returns app status and instance metadata.
- `/ready`: readiness check, verifies the app is ready and Redis is reachable when configured.

### Exercise 5.2: Graceful shutdown

The app registers a SIGTERM handler and runs Uvicorn with `timeout_graceful_shutdown=30`, allowing in-flight requests to complete during container shutdown.

### Exercise 5.3: Stateless design

Conversation history, rate-limit windows, and cost usage are stored through the shared storage layer. With `REDIS_URL`, multiple app instances share the same state.

### Exercise 5.4: Load balancing

The final app can be scaled with Docker Compose:

```bash
docker compose up --build --scale agent=3
docker compose restart nginx
```

Each response includes `served_by`, so requests can be traced to the instance that handled them.

Local verification: scaling to three `agent` containers succeeded, and repeated `/health` requests returned multiple `instance_id` values through Nginx.

### Exercise 5.5: Test stateless

Test flow:

1. Send `/ask` with `user_id="test-user"`.
2. Scale or restart an agent container.
3. Send another `/ask` with the same `user_id`.
4. Conversation history remains available because it is stored in Redis.

Local verification:

```text
Before agent restart: history_count=2
After agent restart:  history_count=4
Storage reported by /health and /ready: redis
```
