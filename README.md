# CloudShield ECS2 — Target Demo Store 2 + telemetry agent + iperf3

Independent Ubuntu 24.04 ECS: works standalone with `sudo bash install.sh`, no accounts, no real payments. Product catalog, cart/checkout, search, login exercise, bounded latency, file transfers and metrics are **real HTTP responses**. `agent` reads host /proc counters and pushes CPU, RAM and network byte totals every 10 seconds when connected.

## Installation

```bash
unzip -q CloudShield_ECS2_Target_v3.zip
cd CloudShield_ECS2_Target_v3
sudo bash install.sh
```

To configure outbound telemetry **before installing**, retrieve ECS1 telemetry token using `sudo grep '^TELEMETRY_TOKEN=' .env` on ECS1. Then run, replacing values:

```bash
sudo CLOUDSHIELD_RECEIVER=http://ECS1_PRIVATE_IP:9108 TELEMETRY_TOKEN=PASTE_ECS1_TELEMETRY_TOKEN bash install.sh
```

ECS1 telemetry receiver must be reachable on private VPC port 9108; only the ingest route is exposed. Grant ECS2 private IP access to 9108 in ECS1 Huawei security group. This example uses HTTP within a controlled VPC; TLS should be configured for non-lab or less trusted networks.

ECS2 application: `http://ECS2_PRIVATE_IP:8081`; health `http://ECS2_PRIVATE_IP:8081/health`.
iperf3 TCP/UDP server `ECS2_PRIVATE_IP:5201` (only ECS1 permitted). For browser use SSH `ssh -L 8081:127.0.0.1:8081 ubuntu@ECS2_PUBLIC_IP`.

**Security groups:** Inbound 8081/tcp and 5201/tcp+udp only from ECS1 private IP /32. Keep 22/tcp limited to instructor IP. Do not open these ports to `0.0.0.0/0`.

## Tests

```bash
curl -i http://127.0.0.1:8081/health
curl -s http://127.0.0.1:8081/api/products
sudo docker compose ps
sudo docker compose logs --tail=50 agent
```

No secret or business data is transmitted in telemetry. The ECS1 dashboard is not exposed by the ingestion port.

### One-command ECS2 acceptance

```bash
sudo bash scripts/acceptance.sh
```

This checks the actual running store's HTTP health, product API and Prometheus metrics and shows container/agent status. With telemetry configured, verify actual HTTP 200 push in the agent logs and ECS1 `/api/v3/telemetry` response. Live deployment is required to verify network routing and Huawei security-group rules.
