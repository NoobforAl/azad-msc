# Course Registration Platform (running project)

One small system that every module of *Advanced Software Engineering* changes. Each module's labs start from a Git tag and end on the next one.

| Tag | Module | What it adds |
|---|---|---|
| `m0` | 00-setup | this skeleton: Go API, Python analytics stub, Makefile, Docker, CI template |
| `m1` … `m8` | 01–08 | see `../PLAN.md`, section 2 |

## Layout

```
project/
  cmd/registration-api/   HTTP entry point (GET /healthz, GET /courses)
  internal/catalog/       in-memory course catalog (replaced by PostgreSQL in module 04)
  analytics/              Python analytics stub (fill rate of courses)
  ci/github-actions.yml   CI template used in module 01, lab 02
  Makefile  Dockerfile  docker-compose.yml
```

## Run

```bash
make check      # go vet + ruff, then go test + python unittest
make run        # API on :8080
curl localhost:8080/courses
```

Requirements: Go ≥ 1.22, Python ≥ 3.8, `ruff`. Docker is optional (`docker compose up --build`).
