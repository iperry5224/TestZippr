# EC2 HTTPS Setup (Direct Access Only)

## What This Does

- **Direct access** (no "ngrok" in URL): `https://18.232.122.255:8443` (SAELAR) and `https://18.232.122.255:8444` (SOPRA)
- **ngrok** (unchanged): `https://saelar.ngrok.dev` and `https://sopra.ngrok.dev` continue to work
- Uses nginx reverse proxy; Streamlit and ngrok config stay as-is

## How to Enable

From project root:

```powershell
.\enable_ec2_https.ps1
```

This will:
1. Generate self-signed SSL certs on EC2
2. Install nginx (if needed) and deploy HTTPS reverse proxy config
3. Open ports 8443, 8444 in security group

## Browser Behavior

- **Direct URL**: Browser may show "Your connection is not private" for self-signed cert. Click **Advanced** → **Proceed**.
- **ngrok URL**: No change; ngrok provides its own trusted cert.

## Files

| File | Purpose |
|------|---------|
| `ec2_ssl_setup.sh` | Generates certs on EC2 |
| `ec2_nginx_https.conf` | nginx HTTPS reverse proxy for 8443→8484, 8444→8080 |
| `enable_ec2_https.ps1` | Master deployment script |
