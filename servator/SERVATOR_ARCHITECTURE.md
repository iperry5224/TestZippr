# Servator Architecture

## Overview

Servator is a modular, cost-conscious AI security platform for retail. Designed for grocery franchises with ~$1M in annual theft losses.

---

## Core Modules

### 1. SCO Vision (Self-Checkout Anomaly Detection)

**Input:** Video from existing SCO cameras  
**Output:** Alerts for suspicious behavior (bagging without scan, barcode switching, rapid voids)

**Tech:**
- Edge inference (Jetson, Coral, or lightweight GPU)
- Object detection + action recognition
- Configurable sensitivity per store

**Deployment:** 1 edge device per 4–8 SCO lanes

---

### 2. Shelf Monitor

**Input:** Aisle cameras (high-shrink categories)  
**Output:** Alerts for bulk grabs, shelf clearing, obscured activity

**Tech:**
- Before/after shelf state comparison
- Anomaly detection on shelf density
- Focus: alcohol, OTC, baby formula, meat, cosmetics

**Deployment:** Targeted aisles only (cost control)

---

### 3. Predictive Analytics Engine

**Input:** POS, inventory, incident reports, time-of-day  
**Output:** Risk scores by SKU, aisle, shift, store

**Tech:**
- Time-series + anomaly models
- No new hardware—uses existing data
- Centralized model, per-store tuning

---

### 4. Exit Verification

**Input:** Overhead camera(s) at each exit; receipt data (barcode/OCR)  
**Output:** Cart-receipt alignment alerts; variance confidence score

**Tech:**
- 1080p+ camera per exit lane
- Edge inference (item detection + receipt OCR)
- Low-confidence events flagged for review, not intervention

**Deployment:** 1 camera per exit; minimal customer interaction

---

### 5. Internal Patterns (POS Analytics)

**Input:** POS data (voids, refunds, discounts, no-receipt returns)  
**Output:** Pattern alerts for process exceptions; no individual targeting

**Tech:**
- Anomaly detection on transaction patterns
- Aggregate only; no employee identification in UI

---

### 6. Command Center (Dashboard)

**Input:** All module outputs  
**Output:** Unified view, recommended actions, trend analytics

**Tech:**
- Streamlit (control center UI)
- Neutral language ("operational event", "process exception")
- Back-office only; customer-invisible

---

## Data Flow

```
[Store Cameras] ──► [Edge Devices] ──► [Local Alerts]
        │                    │
        └────────────────────┼─────────────────────┐
                             │                     │
[POS / Inventory] ───────────┼─────────────────────┼──► [Analytics Engine]
                             │                     │
                             ▼                     ▼
                    [Command Center] ◄── [Aggregated Data]
                     (Dashboard, Alerts, Reports)
```

---

## Deployment Options

| Mode | Use Case | Cost |
|------|----------|------|
| **Edge** | Per-store inference, low latency | Hardware per store |
| **Hybrid** | Edge for vision, cloud for analytics | Balanced |
| **Cloud** | Centralized, smaller stores | Subscription |

---

## Scalability

- **Store-level:** One config per store; same stack everywhere
- **Franchise-level:** Multi-tenant; regional rollups
- **Pilot-first:** Deploy 1–2 stores, measure ROI, then scale

---

## Security & Privacy

- Video processed at edge; only alerts/metadata sent to cloud (if used)
- No PII in analytics; aggregate patterns only
- Compliance: SOC 2, PCI scope (if applicable)
