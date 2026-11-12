#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
code=$(curl -sS -o /tmp/cloudshield-ecs2-health.json -w '%{http_code}' http://127.0.0.1:8081/health)
[[ "$code" = 200 ]] || { echo "FAIL: ECS2 health ($code)"; exit 1; }
code=$(curl -sS -o /tmp/cloudshield-ecs2-products.json -w '%{http_code}' http://127.0.0.1:8081/api/products)
[[ "$code" = 200 ]] || { echo "FAIL: product catalog ($code)"; exit 1; }
code=$(curl -sS -o /dev/null -w '%{http_code}' http://127.0.0.1:8081/metrics)
[[ "$code" = 200 ]] || { echo "FAIL: store metrics ($code)"; exit 1; }
docker compose ps
printf '\nPASS ECS2 store health, catalog and metrics.\n'
if [[ -f .env ]] && grep -q '^CLOUDSHIELD_RECEIVER=http' .env; then
 echo 'Telemetry is configured; check last 50 agent logs for HTTP 200 push:'
 docker compose logs --no-color --tail=50 agent
else
 echo 'Telemetry is not configured (ECS2 standalone mode).'
fi
