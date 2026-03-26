# SOPRA — Full bundle install on EC2

## Build the zip (on your dev machine)

```bash
python create_sopra_full_install_zip.py
```

Output: **`sopra_full_install.zip`**

## Deploy on the other tenant

```bash
unzip -o sopra_full_install.zip -d SOPRA
cd SOPRA
chmod +x install_sopra.sh start_sopra.sh
./install_sopra.sh
./start_sopra.sh
```

- Default URL: **`http://<instance-ip>:8080`**
- Different port (e.g. 8180): `export SOPRA_PORT=8180 && ./start_sopra.sh`
- Open the chosen port in the **security group**.

## What’s inside the bundle

| Item | Purpose |
|------|---------|
| `sopra_setup.py`, `sopra_controls.py` | Entry point and control library |
| `risk_score_*.py`, `cisa_kev_checker.py`, `ssp_generator.py`, `wordy.py` | Shared features |
| `sopra/` | Application package (pages, ISSO, theme, etc.) |
| `assets/`, `.streamlit/`, `templates/`, `demo_csv_data/` | UI assets and samples |
| `requirements.txt` | Base dependencies |
| `kev_catalog_cache.json` | Included if present in repo |
| `install_sopra.sh` | Creates `venv`, installs deps + Streamlit ≥ 1.27 |
| `start_sopra.sh` | Runs Streamlit with `sopra_setup.py` |

## Incremental updates later

For day-to-day syncs (smaller artifact), use:

```bash
python create_sopra_ec2_update.py
```

That produces **`sopra_ec2_update.zip`** (no install scripts; assumes existing venv and layout).

## AWS

SOPRA AI features use **AWS Bedrock** — attach an instance profile (or credentials) with Bedrock invoke permissions in the target region.
