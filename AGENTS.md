# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

TestZippr is a Python 3.12 / Streamlit monorepo containing two primary security assessment applications and several satellite tools. No database is required — state is persisted via JSON files on disk and Streamlit session state.

### Primary applications

| App | Entry point | Default port | Run command |
|-----|-------------|-------------|-------------|
| **SAELAR** (NIST 800-53 assessment) | `nist_setup.py` | 8484 | `streamlit run nist_setup.py --server.port 8484 --server.headless true` |
| **SOPRA** (GRC / ISSO automation) | `sopra_setup.py` | 8080 | `streamlit run sopra_setup.py --server.port 8080 --server.headless true` |

### Virtual environment

The project uses a standard Python venv at `.venv` (not the `security-venv` referenced by some legacy scripts). Activate with:

```bash
source /workspace/.venv/bin/activate
```

### Dependencies

All Python dependencies are in `requirements.txt`. Additional useful packages not in the file but used by some features: `numpy`, `openpyxl`, `XlsxWriter`, `requests`.

### Running tests

```bash
source /workspace/.venv/bin/activate
python test_imports.py                # Quick import smoke test
python test_saelar_integrations.py    # Integration tests (NIST assessor init test requires AWS creds)
```

The NIST assessor init test will fail without AWS credentials — this is expected in environments without AWS configured.

### Lint

No formal linter configuration (no `.flake8`, `pyproject.toml`, `.pylintrc`, etc.) exists in the repo. You can run `python -m py_compile <file>` for syntax checking.

### AWS credentials

AWS credentials are optional for basic app startup and UI navigation. They are required for:
- Running live NIST 800-53 assessments against AWS accounts
- AI-powered features (AWS Bedrock)
- S3 report storage

Without credentials, both apps start and the UI is fully navigable; only features that call AWS APIs will show warnings.

### Gotchas

- `.streamlit/config.toml` sets `server.port = 8080` globally. When running both apps simultaneously, pass `--server.port` explicitly to avoid port conflicts.
- The `setup_environment.sh` script is interactive (prompts for input) and overwrites `requirements.txt` — avoid running it in automated/non-interactive contexts.
- Some install scripts (`install_saelar.sh`, `install_sopra.sh`) create a `venv` directory (not `.venv`). The Cloud Agent environment uses `.venv` instead.
