# SAELAR — Install and Run on a Dedicated EC2 Instance

**Purpose:** Step-by-step instructions to install and run **SAELAR** (Security Assessment Engine for Live AWS Resources) on a **new or separate EC2 instance** (e.g., another AWS account or tenant), not tied to any specific public IP.

**Audience:** Operators deploying from a development machine or CI artifact onto Linux EC2 (Amazon Linux 2 / Ubuntu).

---

## 0. One-shot bundle (recommended)

From the development repo, build **`saelar_full_install.zip`**:

```bash
python create_saelar_full_install_zip.py
```

On the EC2 (or after copying the zip):

```bash
unzip -o saelar_full_install.zip -d SAELAR
cd SAELAR
chmod +x install_saelar.sh start_saelar.sh
./install_saelar.sh    # creates venv, installs all Python dependencies
./start_saelar.sh      # runs Streamlit on port 8484 (override with SAELAR_PORT)
```

The bundle includes all SAELAR Python modules, `assets/`, `.streamlit/`, `templates/`, `demo_csv_data/`, `kev_catalog_cache.json` (if present), `requirements.txt`, plus **`install_saelar.sh`** and **`start_saelar.sh`**.

---

## 1. Prerequisites

| Requirement | Details |
|-------------|---------|
| **OS** | Amazon Linux 2, Ubuntu 20.04+, or similar x86_64 Linux |
| **Python** | **3.8 or newer** strongly recommended. Python 3.7 may work with older dependency pins but is not recommended for current Streamlit. |
| **Network** | Outbound HTTPS to AWS APIs (and Bedrock endpoints in your region). Inbound TCP on the Streamlit port you choose (e.g. **8484** or **8080**) from users or a load balancer. |
| **AWS credentials** | EC2 **instance profile** (preferred) or `~/.aws/credentials` with permissions for SAELAR (STS, Bedrock, IAM, S3, CloudTrail, Config, Security Hub, GuardDuty, etc., per your org’s least-privilege policy). |
| **Shell access** | SSH with `ec2-user` (Amazon Linux) or `ubuntu` (Ubuntu), plus `sudo` if you install systemd units. |

---

## 2. Required Files (Complete Install)

All paths below are **relative to a single application root directory** (e.g. `/home/ec2-user/SAELAR` or `/opt/apps`). **Do not omit files** from this list for a first-time install.

### 2.1 Python modules (repository root)

| File | Role |
|------|------|
| `nist_setup.py` | Application entry point (`streamlit run nist_setup.py`) |
| `nist_dashboard.py` | Dashboard and assessment UI |
| `nist_pages.py` | Additional pages |
| `nist_auth.py` | Authentication / access flow |
| `nist_800_53_controls.py` | Control definitions |
| `nist_800_53_rev5_full.py` | NIST 800-53 Rev 5 assessor engine |
| `risk_score_app.py` | Risk score UI integration |
| `risk_score_calculator.py` | Risk scoring logic |
| `cisa_kev_checker.py` | CISA KEV / BOD 22-01 features |
| `ssp_generator.py` | SSP generation |
| `wordy.py` | Document generation helpers |
| `requirements.txt` | Python dependencies |

### 2.2 Directories

| Path | Role |
|------|------|
| `assets/` | **Required** — contains `saelar_logo.png`, Chad avatars, etc. |
| `.streamlit/` | **Recommended** — `config.toml` / theme (create minimal `config.toml` if missing) |
| `templates/` | **Optional** — include if your deployment package ships Word/document templates |

### 2.3 Optional root files

| File | Role |
|------|------|
| `kev_catalog_cache.json` | Optional local cache for KEV data; app may refresh over the network if absent |
| `start_saelar.sh` | Optional convenience script to launch Streamlit with fixed ports |

> **Important:** The artifact `saelar_ec2_update.zip` produced by `create_saelar_ec2_update.py` contains **only a subset** of these files (incremental updates). For a **new instance**, copy the **full** set above from your development repository or build a **full install archive** that includes every item in §2.1 and `assets/`.

---

## 3. Choose Application Root and Port

Define two values and use them consistently:

| Variable | Example | Notes |
|----------|---------|--------|
| `SAELAR_HOME` | `/home/ec2-user/SAELAR` | Directory containing `nist_setup.py` |
| `SAELAR_PORT` | `8484` | Common choice; **8080** is also used in some environments. Pick one and open it in the security group. |

---

## 4. Installation Steps

### Step 1 — Create application directory and place files

```bash
sudo mkdir -p /home/ec2-user/SAELAR
sudo chown ec2-user:ec2-user /home/ec2-user/SAELAR
cd /home/ec2-user/SAELAR
```

Copy or unzip your **full** SAELAR package here so that `nist_setup.py` is directly under `SAELAR`:

```bash
ls -la nist_setup.py
# Expected: file exists
```

*(On Ubuntu, replace `ec2-user` with `ubuntu` and paths accordingly.)*

### Step 2 — Create a virtual environment

```bash
cd /home/ec2-user/SAELAR
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
```

### Step 3 — Install Python dependencies

```bash
pip install -r requirements.txt
```

Install additional packages commonly required by SAELAR features (if not already satisfied):

```bash
pip install numpy openpyxl XlsxWriter requests
```

### Step 4 — Install a compatible Streamlit version

SAELAR uses `st.rerun()` on current codebases; that API exists in **Streamlit 1.27+**.

```bash
pip install "streamlit>=1.27"
```

If you **cannot** upgrade Streamlit (e.g., old Python), ensure your deployed `nist_setup.py` includes the compatibility shim that maps `st.rerun` to `st.experimental_rerun` for older Streamlit versions.

### Step 5 — Configure AWS region (if needed)

If not using instance metadata defaults:

```bash
export AWS_DEFAULT_REGION=us-east-1   # use your region
```

Add to `~/.bashrc` or the systemd `Environment=` lines if the app should always use a fixed region.

### Step 6 — Verify AWS identity (optional)

```bash
source /home/ec2-user/SAELAR/venv/bin/activate
python -c "import boto3; print(boto3.client('sts').get_caller_identity())"
```

### Step 7 — Open the security group

In the EC2 security group attached to this instance, add an **inbound** rule:

- **Type:** Custom TCP  
- **Port:** `8484` (or the port you chose)  
- **Source:** Your corporate CIDR, VPN range, or the load balancer security group only (avoid `0.0.0.0/0` in production unless required).

---

## 5. Run SAELAR

Always run from `SAELAR_HOME` so relative paths (`assets/`, etc.) resolve correctly.

### 5.1 Foreground (testing)

```bash
cd /home/ec2-user/SAELAR
source venv/bin/activate

streamlit run nist_setup.py \
  --server.port 8484 \
  --server.address 0.0.0.0 \
  --server.headless true \
  --server.fileWatcherType none
```

Press **Ctrl+C** to stop.

### 5.2 Background (simple production)

```bash
cd /home/ec2-user/SAELAR
source venv/bin/activate

nohup streamlit run nist_setup.py \
  --server.port 8484 \
  --server.address 0.0.0.0 \
  --server.headless true \
  --server.fileWatcherType none \
  > /tmp/saelar.log 2>&1 &
```

View logs:

```bash
tail -f /tmp/saelar.log
```

Stop:

```bash
pkill -f 'streamlit run nist_setup'
```

### 5.3 systemd (recommended for production)

Create `/etc/systemd/system/saelar.service`:

```ini
[Unit]
Description=SAELAR - NIST 800-53 Assessment (Streamlit)
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/SAELAR
Environment=HOME=/home/ec2-user
Environment=AWS_DEFAULT_REGION=us-east-1
ExecStart=/home/ec2-user/SAELAR/venv/bin/streamlit run nist_setup.py \
  --server.port 8484 \
  --server.address 0.0.0.0 \
  --server.headless true \
  --server.fileWatcherType none
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Adjust `User`, `WorkingDirectory`, `ExecStart`, and `AWS_DEFAULT_REGION` for your environment.

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable saelar
sudo systemctl start saelar
sudo systemctl status saelar
```

---

## 6. Verification

On the instance:

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8484/
```

Expect **`200`** (or **302** depending on auth redirect).

From your browser (replace host and port):

`http://EC2_PUBLIC_OR_PRIVATE_IP:8484/`

---

## 7. Environment variables (optional)

| Variable | Purpose |
|----------|---------|
| `SAELAR_CERT_DIR` | Directory containing TLS cert/key if terminating TLS in Streamlit |
| `SAELAR_LOGO_PATH` | Override path to logo image |
| `SAELAR_CONFIG_DIR` | Override config directory |
| `SAELAR_AIRGAPPED` | Set to `true` for air-gapped mode (Ollama); see `nist_setup.py` header |

---

## 8. Updating SAELAR later

1. Build **`saelar_ec2_update.zip`** on the development machine:  
   `python create_saelar_ec2_update.py`
2. Copy the zip to the instance and extract **over** `SAELAR_HOME` (preserve `assets/` and `.streamlit/` if not in the zip).
3. Restart the process or `sudo systemctl restart saelar`.

---

## 9. Troubleshooting

| Symptom | Likely cause | Action |
|---------|----------------|--------|
| `ModuleNotFoundError` for `nist_*` or `cisa_kev_checker` | Incomplete file copy | Verify §2 file list |
| `AttributeError: module 'streamlit' has no attribute 'rerun'` | Old Streamlit | Upgrade to `streamlit>=1.27` or deploy code with rerun shim |
| Connection timeout from browser | Security group / NACL | Open inbound port; check corporate firewall |
| Bedrock / AI errors | IAM or region | Confirm Bedrock enabled in region and model access; check instance profile |
| Blank or broken images | Missing `assets/` | Restore `assets/` directory next to `nist_setup.py` |
| `403` / auth loop | `nist_auth.py` configuration | Review auth settings for your environment |

---

## 10. Document control

| Item | Value |
|------|--------|
| **Application** | SAELAR (NIST 800-53 Rev 5, live AWS assessment) |
| **Entry command** | `streamlit run nist_setup.py` |
| **Typical port** | `8484` (or `8080` per organizational standard) |

---

*This guide is intended for operators; adjust usernames, paths, regions, and ports to match the target “other” instance.*
