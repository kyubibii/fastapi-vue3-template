#!/usr/bin/env bash
# Run Alembic migrations inside the running backend container.
set -euo pipefail

docker compose exec backend alembic "$@"
