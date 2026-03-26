# Make It Beautiful in Google Sheets — Step-by-Step Guide

Import the CSV, then follow these steps for a polished, professional sheet with shaded headings.

---

## Step 1: Create the Sheet & Import

1. Go to [sheets.google.com](https://sheets.google.com) → **Blank** (or open a new sheet)
2. **File** → **Import** → **Upload** → select `SAELAR_SOPRA_TIME_ALLOCATION.csv`
3. Choose **Replace spreadsheet** (or **Insert new sheet**)
4. Set separator to **Comma**, click **Import data**

---

## Step 2: Add a Title Row

1. Right-click **Row 1** → **Insert 1 row above**
2. In **A1**, type: `SAELAR & SOPRA Development — Time Allocation Summary`
3. Merge cells: select **A1:D1** → **Format** → **Merge cells** → **Merge all**
4. Center the text, make it **bold**, set font size to **16–18 pt**
5. Optional: give the title row a light fill (e.g., light blue or gray)

---

## Step 3: Add the 70/30 Banner

1. Right-click **Row 2** → **Insert 1 row above**
2. In **A2**, type: `Total Split: 70% Personal Time  |  30% Billable Time`
3. Merge **A2:D2**, center, make **bold**, size **12 pt**
4. Fill color: **Slate blue** or **Indigo 100** (`#E8EAF6`)

---

## Step 4: Shade the Column Headers (Row 4)

1. Select **A4:D4** (Phase, Task, Personal, Billable)
2. **Format** → **Conditional formatting** (or use fill color)
3. **Fill color**: Darker shade — **Slate Blue 700** (`#3949AB`) or **Navy**
4. **Text color**: **White**
5. **Bold** the header text, center align

---

## Step 5: Shade Phase Headers (Phase Names)

1. Select the **Phase** column (Column A)
2. **Format** → **Conditional formatting**
3. **Format cells if** → **Custom formula**:
   ```
   =$A5<>$A4
   ```
   (Adjust row numbers to match your data; this highlights the first row of each phase.)
4. **Formatting style**: Background color **Light blue 100** (`#BBDEFB`) or **Teal 50** (`#E0F2F1`)
5. **Bold** text for phase names

**Alternative (manual):** Fill every first row of each phase section:
- Conceptualizing (rows 5–9): Light blue
- Prototyping (rows 10–15): Light teal
- Coding (rows 16–23): Light green
- Deployment (rows 24–29): Light amber

---

## Step 6: Alternating Row Stripes (Optional)

1. Select your data rows (e.g., A5:D30)
2. **Format** → **Conditional formatting**
3. **Format cells if** → **Custom formula**:
   ```
   =ISEVEN(ROW())
   ```
4. **Formatting style**: Light gray fill (`#F5F5F5`) for even rows

---

## Step 7: Add the Summary Section

1. Below the main table (e.g., row 32), add a blank row
2. **Row 33**: Type `SUMMARY BY PHASE` — merge, bold, larger font
3. **Row 34**: Headers: `Phase` | `Personal (70%)` | `Billable (30%)`
4. **Rows 35–39**: Summary data:
   - Conceptualizing | 92% | 8%
   - Prototyping | 79% | 21%
   - Coding | 69% | 31%
   - Deployment | 66% | 34%
   - **Overall** | **70%** | **30%**
5. Shade the summary header row (row 34) like the main header
6. Bold the **Overall** row

---

## Step 8: Final Polish

- **Column widths**: Double-click column borders to auto-fit
- **Borders**: **Format** → **Borders** → light grid for the data area
- **Number format**: Ensure percentage cells show as `60%` (Format → Number → Percent)
- **Freeze**: **View** → **Freeze** → **2 rows** (keeps title + banner visible when scrolling)

---

## Color Palette Suggestion

| Element | Color | Hex |
|---------|-------|-----|
| Title row | Light gray | `#FAFAFA` |
| 70/30 banner | Indigo 100 | `#E8EAF6` |
| Column headers | Slate Blue 700 | `#3949AB` |
| Phase headers | Light Blue 100 | `#BBDEFB` |
| Alt rows | Gray 50 | `#FAFAFA` |
| Summary header | Teal 700 | `#00796B` |

---

**Done.** You should have a clean, professional sheet with shaded headings and a clear 70/30 split.
