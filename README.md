# TestZippr

Local workspace for **SAELAR-53** deployment scripts, docs, and related tooling.

## Clone

```bash
git clone https://github.com/iperry5224/TestZippr.git
cd TestZippr
```

## SAELAR-53 application source

Canonical app tree for the NIST assessment Streamlit app lives in **`SAELAR-53/`** (entry point: `nist_setup.py`). Regenerate that folder after root changes with:

```bash
python populate_saelar53_folder.py
```

## Notes

- See `.gitignore` for paths excluded from version control (credentials, `security-venv`, private keys, mirrored report trees).
- Regenerate TLS material locally if needed; `*.key` files are not tracked.
