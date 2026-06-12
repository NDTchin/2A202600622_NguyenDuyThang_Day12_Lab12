# Deployment Information

## Public URL

TODO: add Railway or Render URL after deployment.

Local validation URL:

```text
http://localhost:8080
```

## Platform

Railway or Render.

Local Docker Compose stack:

```text
Nginx -> FastAPI agent -> Redis
```

## Test Commands

### Health Check

```bash
curl https://your-agent-url/health
```

Expected response includes:

```json
{"status":"ok"}
```

### Readiness Check

```bash
curl https://your-agent-url/ready
```

### API Test without Authentication

```bash
curl -X POST https://your-agent-url/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"Hello"}'
```

Expected: `401 Unauthorized`.

### API Test with Authentication

```bash
curl -X POST https://your-agent-url/ask \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"Hello"}'
```

Expected: `200 OK`.

### Rate Limit Test

```bash
for i in {1..15}; do
  curl -X POST https://your-agent-url/ask \
    -H "X-API-Key: YOUR_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":\"rate-test\",\"question\":\"test $i\"}"
done
```

Expected: later requests return `429`.

## Environment Variables Set

- `PORT`
- `REDIS_URL`
- `AGENT_API_KEY`
- `JWT_SECRET`
- `OPENAI_API_KEY` if using a real LLM provider
- `LLM_MODEL`
- `RATE_LIMIT_PER_MINUTE`
- `MONTHLY_BUDGET_USD`
- `ALLOWED_ORIGINS`

## Screenshots

- `screenshots/dashboard.png` - TODO after deployment
- `screenshots/running.png` - TODO after deployment
- `screenshots/test.png` - TODO after deployment

## Local Validation Results

Validated locally on June 12, 2026:

- `GET /health` -> `200`
- `GET /ready` -> `200`
- `POST /ask` without API key -> `401`
- `POST /ask` with API key -> `200`
- Rate limit test: `ok=10 limited=2 other=0`
- Redis persistence test: `history_count` remained available after restarting the agent container
- Scaling test: `docker compose up -d --scale agent=3` produced three healthy agent containers behind Nginx
- Day 10 artifact test: `/day10/summary` returns corpus metrics and quality status
