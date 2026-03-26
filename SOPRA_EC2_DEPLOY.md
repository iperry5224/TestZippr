# SOPRA EC2 Deployment Guide

## Critical Success Factors (Don't Skip These)

### 1. SSH User: `ubuntu` (NOT `ec2-user`)
- **SAELAR-SOPRA-Server** uses Ubuntu AMI → SSH user is `ubuntu`
- `ec2-user` will fail with "Permission denied (publickey)"
- Always use: `ubuntu@<EC2_IP>`

### 2. Network Access Required
- SSH and SCP need network permission to reach EC2
- In Cursor/automation: ensure commands run with network access (not sandboxed)
- Commands must be allowed to execute (not just suggested)

### 3. Deploy to Staging First
- Upload files to `/tmp/sopra_update/` on EC2
- Then copy to `/opt/apps/` (production path)
- Avoids path/permission issues during transfer

### 4. Kill Old Process Before Restart
- SOPRA runs as: `streamlit run sopra_setup.py --server.port 8080`
- Use `pkill -f 'streamlit run sopra_setup.py'` to stop
- Wait 2–3 seconds, then start new process
- Otherwise the old code keeps running

### 5. EC2 Layout (SAELAR-SOPRA-Server)
- App path: `/opt/apps/`
- Venv: `/opt/apps/venv`
- SOPRA port: **8080**
- SAELAR port: **8484**
- Start command: `/opt/apps/venv/bin/streamlit run sopra_setup.py --server.port 8080 --server.address 0.0.0.0 --server.headless true`

---

## Quick Deploy Steps

```powershell
# 1. Upload files (from project root)
scp -i saelar-sopra-key.pem sopra_setup.py sopra_controls.py ubuntu@18.232.122.255:/tmp/sopra_update/
scp -i saelar-sopra-key.pem -r sopra demo_csv_data ubuntu@18.232.122.255:/tmp/sopra_update/

# 2. Deploy and restart on EC2
ssh -i saelar-sopra-key.pem ubuntu@18.232.122.255 "pkill -f 'streamlit run sopra_setup.py'; sleep 2; cp -f /tmp/sopra_update/sopra_setup.py /tmp/sopra_update/sopra_controls.py /opt/apps/; rm -rf /opt/apps/sopra; cp -r /tmp/sopra_update/sopra /opt/apps/; cp -r /tmp/sopra_update/demo_csv_data /opt/apps/; cd /opt/apps; nohup /opt/apps/venv/bin/streamlit run sopra_setup.py --server.port 8080 --server.address 0.0.0.0 --server.headless true > /tmp/sopra.log 2>&1 &"
```

---

## Access URLs

| Service | Direct (EC2 IP) | ngrok |
|---------|-----------------|-------|
| SOPRA   | http://18.232.122.255:8080 | https://sopra.ngrok.dev |
| SAELAR  | http://18.232.122.255:8484 | https://saelar.ngrok.dev |

---

## Verify Deployment

1. **Process running:** `ps aux | grep sopra_setup`
2. **ngrok tunnel:** `curl -s http://127.0.0.1:4040/api/tunnels` (or fetch https://sopra.ngrok.dev)
3. **File version:** `head -10 /opt/apps/sopra_setup.py` (check Version in docstring)

---

## Common Failures (and Fixes)

| Failure | Cause | Fix |
|---------|-------|-----|
| Permission denied (publickey) | Wrong SSH user | Use `ubuntu`, not `ec2-user` |
| Connection refused / timeout | Sandbox blocking network | Run with network permission |
| Old code still running | Didn't kill process | `pkill -f 'streamlit run sopra_setup'` before restart |
| Port 8080 not available | Old process still bound | Kill process, wait 2–3 sec, restart |
