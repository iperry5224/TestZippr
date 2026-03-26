# SAE_GRC_Platform_Resource_Provisioning_Requirements

**Document Purpose:** Load balancer target configuration and Streamlit-specific requirements for SAELAR and SOPRA applications.

---

## 1. Load Balancer Target Summary

| Application | Target Resource | Port | Protocol |
|-------------|-----------------|------|----------|
| SAELAR | EC2 instance(s) running sopsael-saelar container | 8443 | HTTP/TCP |
| SOPRA | EC2 instance(s) running sopsael-sopra container | 5224 | HTTP/TCP |

Both applications run as Docker containers on the same EC2 host(s). When using --network host, they listen directly on the host's ports.

---

## 2. Consolidated Configuration Table (Including Streamlit Requirements)

| Configuration | SAELAR | SOPRA |
|---------------|--------|-------|
| Target Resource | EC2 instance(s) / sopsael-saelar container | EC2 instance(s) / sopsael-sopra container |
| Target Port | 8443 | 5224 |
| Protocol | HTTP/TCP | HTTP/TCP |
| Health Check Path | /_stcore/health | /_stcore/health |
| Health Check Method | GET | GET |
| Expected Health Response | HTTP 200 | HTTP 200 |
| WebSocket Support | Required | Required |
| Session Affinity (Sticky Sessions) | Required (if multiple targets) | Required (if multiple targets) |
| Idle Timeout | ≥ 300 seconds recommended | ≥ 300 seconds recommended |
| Forward Headers | X-Forwarded-Proto, X-Forwarded-For | X-Forwarded-Proto, X-Forwarded-For |

---

## 3. Streamlit-Specific Requirements

SAELAR and SOPRA are built with Streamlit. The following requirements apply to load balancer configuration:

| Requirement | Details |
|-------------|---------|
| Health Check Path | Use /_stcore/health — do NOT use / as the health endpoint |
| WebSocket Support | Must be enabled — Streamlit uses WebSockets for real-time UI updates |
| Session Affinity (Sticky Sessions) | Required when multiple backend targets exist — each user session is stateful and must remain pinned to the same backend |
| Idle Timeout | Set to 300+ seconds — WebSocket connections can be long-lived; default 60s may drop active sessions |
| X-Forwarded Headers | Pass X-Forwarded-Proto (e.g., https) and X-Forwarded-For (client IP) when terminating SSL at the load balancer |

---

## 4. Security Group Ports

Allow the following ports for load balancer → target communication:

| Port | Application |
|------|-------------|
| 8443 | SAELAR |
| 5224 | SOPRA |

Optional (management):
- 22 — SSH

---

## 5. Alternate Deployment (Standalone SAELAR)

If SAELAR is deployed in standalone mode (not SOPSAEL):

| Application | Target Port |
|-------------|-------------|
| SAELAR (standalone) | 8484 |

All Streamlit requirements above apply.

---

## 6. Notes for Network Engineering

1. **Health checks** — Target group health checks must use path /_stcore/health. The root path / is not a valid Streamlit health endpoint.
2. **WebSockets** — Both applications require WebSocket upgrade support. Ensure the load balancer does not block or prematurely terminate WebSocket connections.
3. **Sticky sessions** — If the target group has multiple instances, enable stickiness (e.g., 86400 seconds) so all requests for a session hit the same backend.
4. **Idle timeout** — Increase load balancer idle timeout (e.g., 300–4000 seconds for ALB) to prevent closing long-lived Streamlit sessions.
5. **HTTPS termination** — When terminating SSL at the load balancer, configure forwarding of X-Forwarded-Proto and X-Forwarded-For so the applications generate correct URLs.

---

*Document generated for SAE GRC Platform deployment.*
