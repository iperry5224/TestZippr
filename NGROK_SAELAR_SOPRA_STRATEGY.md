# ngrok Tunnels for SAELAR & SOPRA — Failure Analysis & Re-enable Strategy

## Architecture Overview

| Component | Location | Port | ngrok Domain |
|-----------|----------|------|--------------|
| SAELAR | EC2 | 8484 | https://saelar.ngrok.dev |
| SOPRA | EC2 | 8080 | https://sopra.ngrok.dev |
| Igento | EC2 | 8000 | https://igento.ngrok.dev |

**ngrok runs on EC2** — It tunnels localhost:8484 and localhost:8080 to the reserved domains. Reserved domains (saelar.ngrok.dev, sopra.ngrok.dev) can only be claimed by **one** ngrok agent at a time.

---

## Root Cause Analysis

### 1. **ngrok-tunnels Was Stopped**

`fix_igento_ngrok.py` (used to fix Igento tunnel conflicts) explicitly **stops** `ngrok-tunnels` and starts `ngrok-igento` (igento-only):

```
sudo systemctl stop ngrok-tunnels   # ← saelar + sopra tunnels disabled
sudo systemctl start ngrok-igento   # ← only igento.ngrok.dev
```

**Result:** SAELAR and SOPRA tunnels are no longer running on EC2.

### 2. **Domain Conflict (Reserved Domains)**

- Each reserved domain (saelar.ngrok.dev, sopra.ngrok.dev) can only be online in **one** ngrok agent.
- If **local ngrok** on your Windows machine is running with these domains, EC2 ngrok cannot use them.
- If **EC2 ngrok** has them, local ngrok cannot.

### 3. **Service Split**

- `ngrok-tunnels` — Originally: saelar + sopra (deploy_to_aws.py). Later extended to saelar + sopra + igento (deploy_igento_to_aws.py).
- `ngrok-igento` — Igento only. Created to avoid ERR_NGROK_334 "already online" when igento was claimed elsewhere.

### 4. **Possible Config Drift**

- ngrok.yml on EC2 might be missing saelar/sopra tunnels.
- ngrok-tunnels might be trying to start tunnels that conflict with ngrok-igento.

---

## Re-enable Strategy

### Phase 1: Diagnose (Run First)

1. **Check what's running on EC2:**
   ```bash
   ssh -i saelar-sopra-key.pem ubuntu@18.232.122.255 "
     echo '=== ngrok processes ==='
     pgrep -a ngrok || echo '(none)'
     echo ''
     echo '=== Services ==='
     sudo systemctl is-active ngrok-tunnels ngrok-igento saelar sopra 2>/dev/null
     echo ''
     echo '=== Ports ==='
     ss -tlnp | grep -E '8484|8080|8000'
     echo ''
     echo '=== ngrok-tunnels logs ==='
     sudo journalctl -u ngrok-tunnels --no-pager -n 20 2>/dev/null
   "
   ```

2. **Check local ngrok (Windows):**
   - Open Task Manager → look for `ngrok.exe`
   - Or: `Get-Process ngrok -ErrorAction SilentlyContinue`
   - If local ngrok is using saelar/sopra domains, **stop it** so EC2 can use them.

3. **Test direct EC2 access:**
   ```powershell
   curl http://18.232.122.255:8080   # SOPRA
   curl http://18.232.122.255:8484   # SAELAR
   ```
   If these fail, SAELAR/SOPRA apps are down — fix those first.

---

### Phase 2: Choose a Path

| Scenario | Action |
|----------|--------|
| **ngrok-igento running, ngrok-tunnels stopped** | Start ngrok-tunnels with **saelar + sopra only** (no igento). Leave ngrok-igento for igento. |
| **ngrok-tunnels running but failing** | Check logs; kill conflicting ngrok; ensure config has saelar+sopra; restart. |
| **Local ngrok using saelar/sopra** | Stop local ngrok. EC2 ngrok will then be able to claim the domains. |
| **SAELAR/SOPRA not listening** | Restart saelar and sopra services first. |

---

### Phase 3: Fix — Recommended Approach

**Option A: Two Services (Safest)**

- `ngrok-igento` — igento only (already exists)
- `ngrok-saelar-sopra` — saelar + sopra only (new service)

This avoids any conflict: each service owns different domains.

**Option B: Single ngrok-tunnels (All Three)**

- Stop ngrok-igento
- Update ngrok.yml to include saelar, sopra, igento
- Start ngrok-tunnels

---

## Quick Fix Commands

### 1. Run the fix script (creates ngrok-saelar-sopra, starts it)

```powershell
cd c:\Users\iperr\TestZippr
python fix_ngrok_saelar_sopra.py
```

### 2. Manual fix (SSH to EC2)

```bash
# Stop igento-only ngrok (optional — only if you want saelar+sopra in same process as igento)
sudo systemctl stop ngrok-igento

# Ensure ngrok-tunnels config has saelar + sopra
cat /home/ubuntu/.config/ngrok/ngrok.yml
# Should show:
#   tunnels:
#     saelar: addr: 8484, domain: saelar.ngrok.dev
#     sopra:  addr: 8080, domain: sopra.ngrok.dev

# Kill any stray ngrok
sudo pkill -f ngrok
sleep 3

# Start ngrok-tunnels
sudo systemctl start ngrok-tunnels
sleep 8

# Verify
sudo systemctl status ngrok-tunnels
curl -s https://sopra.ngrok.dev | head -5
curl -s https://saelar.ngrok.dev | head -5
```

---

## Verification Checklist

- [ ] SAELAR listening on 8484: `ss -tlnp | grep 8484`
- [ ] SOPRA listening on 8080: `ss -tlnp | grep 8080`
- [ ] ngrok process running: `pgrep -a ngrok`
- [ ] https://sopra.ngrok.dev returns SOPRA page
- [ ] https://saelar.ngrok.dev returns SAELAR page
- [ ] No local ngrok competing for same domains

---

## Related Files

| File | Purpose |
|------|---------|
| `troubleshoot_ngrok.py` | Diagnose + restart ngrok-tunnels |
| `fix_igento_ngrok.py` | Created ngrok-igento (stopped ngrok-tunnels) |
| `fix_ngrok_saelar_sopra.py` | **New** — Re-enable saelar + sopra tunnels |
| `ngrok_no_igento.yml` | Local reference config (saelar, sopra, periculo) |
| `deploy_to_aws.py` | Original ngrok-tunnels setup |
