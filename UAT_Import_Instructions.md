# User Acceptance Test Plans — Google Sheets Import

## Files

| File | Description |
|------|-------------|
| **`UAT_SAELAR_SOPRA_Combined.xlsx`** | **Single file with 2 tabs** — SAELAR (23 tests) + SOPRA (25 tests) |
| `UAT_SAELAR.csv` / `UAT_SOPRA.csv` | Plain CSV (no formatting) |

**Combined file includes:** Fancy headers, column shading, category-colored borders, Pass/Fail dropdowns, auto-filter, frozen header row. Switch between platforms via tabs.

**Black-box testing:** All tests can be executed **without application source code access**. Use the UI, browser DevTools (Network tab), or CLI only.

---

## Import into Google Sheets

1. Go to [Google Sheets](https://sheets.google.com)
2. **File → Import → Upload**
3. Select `UAT_SAELAR_SOPRA_Combined.xlsx`
4. Choose **Replace spreadsheet**
5. Click **Import data** — formatting (colors, fonts) is preserved; both tabs will appear as sheets

---

## Column Definitions

| Column | Purpose |
|--------|---------|
| **Test ID** | Unique identifier (SAE-xxx or SOP-xxx) |
| **No Source Req'd** | ✓ = Test is black-box (UI, browser DevTools, CLI only — no source code needed) |
| **Category** | Security, Relevance, Ease of Use, Functionality, Performance, Compliance |
| **Metric** | Specific evaluation metric |
| **Test Scenario** | What is being tested |
| **Acceptance Criteria** | Success conditions |
| **Steps to Execute** | How to run the test |
| **Expected Result** | What should happen |
| **Pass/Fail** | Tester fills: Pass, Fail, N/A |
| **Notes** | Tester comments |
| **Tester** | Name of tester |
| **Date** | Test date |

---

## Evaluation Categories

Both UAT plans use the same six categories:

- **Security** — Data protection, credentials, session handling, AI transparency
- **Relevance** — Framework alignment, control accuracy, workflow fit
- **Ease of Use** — Navigation, clarity, workflow intuitiveness
- **Functionality** — Features work as designed
- **Performance** — Response time, load time
- **Compliance** — Audit readiness, data residency, FedRAMP alignment

---

## Black-Box Testing Emphasis

All UAT cases are designed for **black-box testing**:

- **UI:** Click through flows, import/export, verify displayed data
- **Browser DevTools:** Network tab for inspecting outbound requests (e.g. AI/cloud calls), console for errors
- **CLI / env:** Configure credentials, toggle air-gapped mode, run assessment scripts

No need to read or modify application source code. Testers can validate behavior from the outside.

---

## Usage Tips

1. **Freeze header row** — View → Freeze → 1 row
2. **Add filters** — Select header row → Data → Create a filter
3. **Conditional formatting** — Highlight Pass (green) and Fail (red) in the Pass/Fail column
4. **Duplicate** — Copy the sheet to create versions (e.g., "UAT SAELAR v1.0", "UAT SOPRA Pre-Release")
