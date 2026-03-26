# SAELAR-53

SAELAR-53 application source (NIST 800-53 Rev 5 assessment Streamlit app).

## Entry point

- **Main app:** `nist_setup.py`

## Run (after venv + deps)

```bash
cd SAELAR-53
python -m venv venv
source venv/bin/activate   # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
streamlit run nist_setup.py
```

## Linux EC2 one-shot

```bash
chmod +x install_saelar.sh start_saelar.sh
./install_saelar.sh
./start_saelar.sh
```

This folder is synced from the repo root using `populate_saelar53_folder.py` (same file list as `create_saelar_full_install_zip.py`).
