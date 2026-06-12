# Lab 12 - Complete Production Agent

This folder contains the final production-ready agent for the Day 12 deployment lab.

## Checklist Deliverable

- [x] Multi-stage Dockerfile
- [x] Docker Compose stack: Nginx, agent, Redis
- [x] `.dockerignore`
- [x] Health check endpoint: `GET /health`
- [x] Readiness endpoint: `GET /ready`
- [x] API key authentication
- [x] Rate limiting: default `10 req/min`
- [x] Cost guard: default `$10/month`
- [x] Environment-based configuration
- [x] Structured JSON logging
- [x] Graceful shutdown
- [x] Stateless state storage through Redis
- [x] Railway and Render deployment config

## Structure

```text
06-lab-complete/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── auth.py
│   ├── rate_limiter.py
│   ├── cost_guard.py
│   └── storage.py
├── utils/
│   └── mock_llm.py
├── Dockerfile
├── docker-compose.yml
├── nginx.conf
├── railway.toml
├── render.yaml
├── .env.example
├── .dockerignore
└── requirements.txt
```

## Run Locally with Docker Compose

```bash
docker compose up --build
```

Test through Nginx:

```bash
curl http://localhost:8080/health
curl http://localhost:8080/ready
```

Test the protected agent endpoint:

```bash
curl -X POST http://localhost:8080/ask \
  -H "X-API-Key: local-dev-key" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"What is deployment?"}'
```

The `/ask` endpoint answers from the Day 10 cleaned scholarly-paper corpus and
returns matched source papers in the `sources` field.

Inspect the deployed Day 10 artifacts:

```powershell
Invoke-RestMethod `
  -Uri "http://localhost:8080/day10/summary" `
  -Headers @{ "X-API-Key" = "local-dev-key" }

Invoke-RestMethod `
  -Uri "http://localhost:8080/day10/search?q=deep%20learning" `
  -Headers @{ "X-API-Key" = "local-dev-key" }

Invoke-RestMethod `
  -Uri "http://localhost:8080/day10/report/phase1" `
  -Headers @{ "X-API-Key" = "local-dev-key" }
```

Run the local self-test script from the repository root:

```powershell
.\06-lab-complete\test-local.ps1
```

Scale the app:

```bash
docker compose up --build --scale agent=3
docker compose restart nginx
```

Restarting Nginx after scaling lets it resolve the current agent replicas.

## Run Locally without Docker

```bash
pip install -r requirements.txt
set AGENT_API_KEY=local-dev-key
python -m app.main
```

Then call `http://localhost:8000`.

## Deploy Railway

```bash
railway login
railway init
railway variables set AGENT_API_KEY=your-secret-key
railway variables set JWT_SECRET=your-jwt-secret
railway variables set RATE_LIMIT_PER_MINUTE=10
railway variables set MONTHLY_BUDGET_USD=10.0
railway up
railway domain
```

Set `REDIS_URL` if using a managed Redis plugin/service.

## Deploy Render

1. Push the repo to GitHub.
2. Create a new Render Blueprint.
3. Connect the repo and let Render read `render.yaml`.
4. Set `REDIS_URL` and any real provider secrets.
5. Deploy and copy the public URL into `DEPLOYMENT.md`.

## Production Readiness Check

```bash
python check_production_ready.py
```
