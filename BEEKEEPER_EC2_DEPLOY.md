# BeeKeeper EC2 Deployment

## Deployed

BeeKeeper is deployed to EC2 in `/opt/apps/beekeeper` and runs on **port 2323**.

## Access

| Environment | URL |
|-------------|-----|
| **Cloud (EC2)** | http://18.232.122.255:2323 |
| **Local** | `run beekeeper` then http://localhost:8501 (or port shown) |

## Deploy / Update

From project root:

```powershell
.\deploy_beekeeper_to_ec2.ps1
```

This script:
1. Ensures port 2323 is open in the security group (`saelar-sopra-sg`)
2. Copies `container_xray_app.py` and `container_xray/` to EC2
3. Deploys to `/opt/apps/beekeeper`
4. Restarts BeeKeeper on port 2323

## EC2 Layout

```
/opt/apps/beekeeper/
├── container_xray_app.py
└── container_xray/
    ├── __init__.py
    ├── scanner.py
    ├── ai_engine.py
    └── assets/
        └── beekeeper_logo.png
```

Uses shared venv: `/opt/apps/venv`

## Verify

```bash
ssh -i saelar-sopra-key.pem ubuntu@18.232.122.255 "ss -tlnp | grep 2323; curl -s -o /dev/null -w '%{http_code}' http://localhost:2323/"
```

## Security Group

Port **2323** must be open. Run `py ensure_ec2_ports_open.py` to add it if missing.

## Troubleshooting: ERR_CONNECTION_REFUSED

If http://18.232.122.255:2323 fails with "connection refused":

1. **Network/Firewall:** Some corporate or home networks block direct IP access to cloud hosts. Try from another network (e.g. mobile hotspot) or use ngrok.
2. **Add BeeKeeper to ngrok:** If you use ngrok on EC2 for SAELAR/SOPRA, add a beekeeper tunnel to your ngrok config and restart ngrok-tunnels.
3. **Verify on EC2:**  
   `ssh -i saelar-sopra-key.pem ubuntu@18.232.122.255 "sudo systemctl status beekeeper; curl -s -o /dev/null -w '%{http_code}' http://localhost:2323/"`
