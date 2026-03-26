# SAELAR User Manual – Screenshot Guide

Place PNG screenshots in `user_manuals/screenshots/saelar/` with these exact filenames. Then run `python generate_user_manuals.py` to rebuild the manual.

## Filenames and What to Capture

| Filename | Slide | What to Capture |
|----------|-------|-----------------|
| `01_what_is.png` | What is SAELAR? | Splash screen with logo, or main dashboard after login |
| `02_getting_started.png` | Getting Started | Sidebar with System info section + control family selector (or splash/disclaimer) |
| `03_main_tabs.png` | Main Tabs | Tab bar showing: NIST Assessment, AWS Console, Chad, Risk Calculator, SSP Generator, BOD 22-01 |
| `04_nist_assessment.png` | NIST Assessment Workflow | NIST Assessment tab – control families selected, Run Assessment button, sample results |
| `05_chad.png` | Chad AI Assistant | Chad tab – chat interface with a sample question/response |
| `06_ssp_poam.png` | SSP Generator & POA&Ms | SSP Generator tab – Generate SSP and/or POA&Ms sub-tab |
| `07_bod_kev.png` | BOD 22-01 (KEV) | BOD 22-01 tab – Check CVEs or KEV Dashboard |
| `08_tips.png` | Tips for ISSOs | Sidebar with system info populated, or any helpful overview |
| `09_need_help.png` | Need Help? | AWS config page or support/contact info |

## Taking Screenshots

1. Open SAELAR (e.g., https://saelar.ngrok.dev or your local URL)
2. Navigate to the screen described above
3. Use **Windows + Shift + S** (Snipping Tool) or **Print Screen** to capture
4. Save as PNG in `user_manuals/screenshots/saelar/` with the exact filename
5. Run: `python generate_user_manuals.py`

## Tips

- Use **wide/browser window** for best results (slides are 10" x 7.5")
- Crop to the relevant UI area; avoid empty space
- PNG preferred for clean text and UI elements
