# Container Xray Lite

AI-powered container security scanner — JFrog Xray–style capabilities for enterprises that lack managed container/Docker tooling.

## Features

| Capability | Description |
|------------|-------------|
| **Vulnerability scanning** | Scans container images via Trivy or Grype for CVEs and package-level issues |
| **AI contextual analysis** | Bedrock (or Ollama) analyzes results for exploitability, prioritization, and risk |
| **AI remediation** | Per-vulnerability remediation guidance (Dockerfile fixes, alternatives, verification) |
| **Policy recommendations** | AI-suggested deployment gates, CI/CD thresholds, registry controls |
| **Supply chain narrative** | SBOM-style narrative on dependency risk and trust boundaries |

## Prerequisites

1. **Scanner** (pick one):
   - [Trivy](https://trivy.dev/docs/installation/) — `scoop install trivy` (Windows) or see Trivy docs
   - [Grype](https://github.com/anchore/grype#installation)

2. **AI backend** (pick one):
   - **AWS Bedrock** — Uses boto3 with default credentials (IAM role or `aws configure`)
   - **Ollama** (air-gapped) — Set `CONTAINER_XRAY_AIRGAPPED=true`, run `ollama serve`, pull `llama3:8b`

## Quick Start

```powershell
cd c:\Users\iperr\TestZippr
streamlit run container_xray_app.py
```

1. Enter a container image (e.g. `nginx:latest`, `alpine:3.18`, `myregistry.io/app:v1`)
2. Click **Run Scan**
3. Review findings in the **Findings** tab
4. Use **AI Analysis** for executive summary, prioritization
5. Use **Policy** for deployment recommendations
6. Use **Supply Chain** for SBOM-style narrative

## Air-Gapped Mode

For environments without AWS:

```powershell
$env:CONTAINER_XRAY_AIRGAPPED = "true"
ollama serve
ollama pull llama3:8b
streamlit run container_xray_app.py
```

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Container      │     │  Trivy / Grype    │     │  Bedrock /       │
│  Image          │────▶│  (subprocess)     │────▶│  Ollama          │
│  (Docker ref)   │     │  JSON output      │     │  AI analysis     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                          │
                                                          ▼
                                                 ┌──────────────────┐
                                                 │  Streamlit UI     │
                                                 │  Findings, AI,   │
                                                 │  Policy, SBOM     │
                                                 └──────────────────┘
```

## JFrog Xray Parallels

| Xray Feature | Container Xray Lite |
|--------------|---------------------|
| Container scanning | Trivy/Grype |
| Vulnerability DB | Via Trivy/Grype (NVD, etc.) |
| Prioritization | AI contextual analysis |
| Remediation | AI per-finding guidance |
| Policy / gates | AI policy recommendations |
| SBOM | AI supply chain narrative |
| License compliance | *(Future)* |

## Files

- `container_xray/scanner.py` — Trivy/Grype integration, JSON parsing
- `container_xray/ai_engine.py` — Bedrock/Ollama calls, prompts
- `container_xray_app.py` — Streamlit UI
