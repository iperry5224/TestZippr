# CSTA/NIH Application Access – Port Clarification for Network Team

**Environment:** CSTA (acct 7515) at 10.40.25.221  
**Ticket:** NIHS-260

---

## Why the Confusion

There are two deployment architectures in our docs; they use different ports:

| Deployment Type | SAELAR Port | SOPRA Port | BeeKeeper Port |
|-----------------|-------------|------------|----------------|
| **Non-containerized** (EC2 venv, systemd) | **8484** | **8080** | **2323** |
| **Containerized** (Docker/sopsael) | **8443** | **5224** | N/A |

- **SAE_GRC_Platform_Resource_Provisioning_Requirements.md** and Pavlos’s table describe the **containerized** setup (8443, 5224).
- Gefter’s testing showed nothing on 8443 and SAELAR running on **8080** on 10.40.25.221, which indicates a **non-containerized** setup.

---

## Definitive Port Mapping for CSTA (10.40.25.221)

**If CSTA uses the non-containerized deployment (EC2 venv, systemd):**

| Application | Port | Protocol | Notes |
|-------------|------|----------|-------|
| SAELAR | **8484** | HTTP/TCP | Streamlit; WebSockets on same port |
| SOPRA | **8080** | HTTP/TCP | Streamlit; WebSockets on same port |
| BeeKeeper | **2323** | HTTP/TCP | When deployed |

**Target:** Same EC2 instance for all three applications.

---

## Action Required: Verify CSTA Deployment

Before finalizing with the Network team, confirm what is actually running on 10.40.25.221:

```bash
# From a host that can reach 10.40.25.221:
ss -tlnp | grep -E '8484|8080|8443|5224|2323'
# or
curl -s -o /dev/null -w '%{http_code}' http://10.40.25.221:8484/   # SAELAR
curl -s -o /dev/null -w '%{http_code}' http://10.40.25.221:8080/   # SOPRA
```

- If 8484 and 8080 respond → use **non-containerized** mapping above.  
- If 8443 and 5224 respond → use **containerized** mapping (8443, 5224).

---

## Suggested Message for Network Team

**Subject:** NIHS-260 – Clarification: Target Ports for CSTA (10.40.25.221)

Hi Pavlos / Gefter,

There are two deployment variants in our documentation, which caused the port confusion. For the CSTA environment at **10.40.25.221**, here is the port mapping:

**Current CSTA deployment (non-containerized):**

| Application | Target Port | Protocol |
|-------------|-------------|----------|
| SAELAR | **8484** | HTTP/TCP |
| SOPRA | **8080** | HTTP/TCP |
| BeeKeeper | **2323** | HTTP/TCP (when ready) |

**Target:** Single EC2 instance; all apps on the same host.

**Streamlit requirements:**
- Health check path: **/_stcore/health** (not /)
- WebSocket support required (Streamlit uses HTTP upgrade on the same port)
- Idle timeout: ≥ 300 seconds recommended

**Target Group / Security Group:**
- The EC2 security group must allow inbound traffic from the ALB/Target Group CIDR on ports 8484, 8080, (and 2323 when BeeKeeper is added).
- For internal ALBs, the Target Group should register the instance’s **private IP** (not public).

Please share the CIDR or subnet the Target Group uses so we can add it to the EC2 security group if needed.

Thanks,  
Ira
