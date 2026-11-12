#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ $(id -u) -ne 0 ]]; then echo 'Run: sudo bash install.sh'; exit 1; fi
if ! command -v docker >/dev/null || ! docker compose version >/dev/null 2>&1; then
  apt-get update -qq; DEBIAN_FRONTEND=noninteractive apt-get install -y -qq docker.io docker-compose-v2 curl
  systemctl enable --now docker
fi
if [[ ! -f .env ]]; then
  umask 077
  cat >.env <<EOF
STORE_BIND_IP=0.0.0.0
IPERF_BIND_IP=0.0.0.0
CLOUDSHIELD_RECEIVER=${CLOUDSHIELD_RECEIVER:-}
TELEMETRY_TOKEN=${TELEMETRY_TOKEN:-}
EOF
fi
# ECS1 integration optional. Values passed during install persist for future restarts.
if [[ -n "${CLOUDSHIELD_RECEIVER:-}" ]]; then sed -i "/^CLOUDSHIELD_RECEIVER=/d" .env; printf 'CLOUDSHIELD_RECEIVER=%s\n' "$CLOUDSHIELD_RECEIVER" >>.env; fi
if [[ -n "${TELEMETRY_TOKEN:-}" ]]; then sed -i "/^TELEMETRY_TOKEN=/d" .env; printf 'TELEMETRY_TOKEN=%s\n' "$TELEMETRY_TOKEN" >>.env; fi
chmod 600 .env
[ -n "$(command -v curl || true)" ] || (apt-get update -qq && apt-get install -y -qq curl)
docker compose config --quiet
docker compose build
docker compose up -d --no-build
for i in $(seq 1 30);do if curl -fsS --max-time 3 http://127.0.0.1:8081/health >/dev/null 2>&1;then break;fi;sleep 2;done
curl -fsS http://127.0.0.1:8081/health
echo; echo 'Target Demo Store 2: http://ECS2_PRIVATE_IP:8081'
echo 'iperf3 receiver: ECS2_PRIVATE_IP:5201 (TCP/UDP)'
echo 'Outbound telemetry agent sends every 10 sec if CLOUDSHIELD_RECEIVER and TELEMETRY_TOKEN are set.'
echo 'SECURITY: Restrict inbound 8081 and 5201 in Huawei security group to ECS1 private IP only.'
