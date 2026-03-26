# Servator Control Center – Design Principles

## Invisible Presence

Store patrons should not feel surveilled. Servator is designed to be **customer-invisible**:

| Avoid | Use Instead |
|-------|-------------|
| "Theft" | "Operational event" / "Process exception" |
| "Suspicious" | "Activity variance" / "Pattern anomaly" |
| "Caught" | "Loss prevented" / "Variance flagged" |
| "Surveillance" | "Operational intelligence" / "Loss prevention analytics" |

**Back-office only.** The dashboard runs in the security control center. No customer-facing displays. No confrontational messaging.

**No PII.** Analytics use aggregate patterns. No customer identification in alerts or reports.

**Low-confidence handling.** Exit verification and similar modules flag "variance—low confidence" rather than accusatory alerts. Staff review before any action.

---

## Wow Factor (Control Center)

- **Executive summary** – At-a-glance metrics: events, loss prevented, focus areas, risk index
- **Recommended actions** – What to do next, with reasoning (not raw alerts)
- **Trend context** – "↓12% vs prior day" so LP knows if things are improving
- **Professional aesthetic** – Dark, calm, control-room feel; not alarm-heavy

---

## Meaningful Insights

- **Est. loss prevented** – Connects activity to dollar impact
- **Focus areas** – Which aisle, which lane, which hour
- **Staffing alignment** – "Historical peak for events; consider visibility"
- **Process exceptions** – Frames SCO issues as training opportunities, not blame
