# TestZippr

A Streamlit-based cybersecurity compliance suite for NIST assessments, AWS security posture review, risk calculation, and System Security Plan (SSP) generation.

## Features

- **NIST Assessment** – Self-assess against NIST 800-171 / 800-53 control families with import/export support.
- **AWS Console** – Connect to AWS Security Hub to pull and review findings, or import findings from JSON.
- **Chad (AI)** – AI-powered compliance assistant that answers questions about NIST frameworks, CMMC, SSPs, and more.
- **Risk Calculator** – Evaluate threats with a likelihood × impact matrix and visualize your risk posture.
- **SSP Generator** – Build a System Security Plan document section by section, with JSON and DOCX export.

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Project Structure

```
app.py                  # Main Streamlit entry point
requirements.txt        # Python dependencies
.streamlit/config.toml  # Streamlit theme and server config
tabs/
  nist_assessment.py    # NIST compliance assessment tab
  aws_console.py        # AWS Security Hub integration tab
  chad_ai.py            # AI compliance assistant tab
  risk_calculator.py    # Risk scoring and matrix tab
  ssp_generator.py      # SSP document builder and exporter
utils/
  file_io.py            # Robust file I/O with retry logic (guards against Errno 5)
```

## Error Handling

The application includes robust I/O error handling throughout, specifically addressing `[Errno 5] Input/output error` issues that can occur with:

- Uploaded file buffer consumption (Streamlit `UploadedFile` objects)
- Temporary file creation on unreliable storage (container volume mounts, network drives)
- Document generation (DOCX export uses in-memory `BytesIO` buffers to avoid filesystem I/O)

All file operations use the `utils/file_io.py` module which provides retry logic with exponential backoff.
