#!/usr/bin/env python3
"""Generate branded graphics for user manual slides (when screenshots unavailable)."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
OUTPUT = ROOT / "user_manuals" / "screenshots"
W = 800
H = 600

# SAELAR brand colors
SAELAR_BLUE = (26, 82, 156)
SAELAR_LIGHT = (59, 130, 246)
SAELAR_DARK = (30, 58, 138)
BG_GRADIENT_TOP = (241, 245, 249)
BG_GRADIENT_BOT = (226, 232, 240)


def create_gradient_bg(w, h):
    """Create a subtle gradient background."""
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        r = int(BG_GRADIENT_TOP[0] + (BG_GRADIENT_BOT[0] - BG_GRADIENT_TOP[0]) * y / h)
        g = int(BG_GRADIENT_TOP[1] + (BG_GRADIENT_BOT[1] - BG_GRADIENT_TOP[1]) * y / h)
        b = int(BG_GRADIENT_TOP[2] + (BG_GRADIENT_BOT[2] - BG_GRADIENT_TOP[2]) * y / h)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return img


def create_saelar_card(title, icon_text, filename):
    """Create a branded card graphic for a slide."""
    img = create_gradient_bg(W, H)
    draw = ImageDraw.Draw(img)
    
    # Accent bar (top)
    draw.rectangle([0, 0, W, 8], fill=SAELAR_BLUE)
    
    # Rounded card area
    margin = 40
    card_top, card_left = 60, margin
    card_w, card_h = W - 2 * margin, H - 120
    draw.rounded_rectangle([card_left, card_top, card_left + card_w, card_top + card_h],
                          radius=16, fill=(255, 255, 255), outline=SAELAR_LIGHT, width=2)
    
    # Icon circle
    icon_cx, icon_cy = W // 2, card_top + 80
    draw.ellipse([icon_cx - 60, icon_cy - 60, icon_cx + 60, icon_cy + 60],
                 fill=SAELAR_BLUE, outline=SAELAR_DARK, width=2)
    
    # Try to use a font
    try:
        font_lg = ImageFont.truetype("arial.ttf", 48)
        font_md = ImageFont.truetype("arial.ttf", 28)
        font_sm = ImageFont.truetype("arial.ttf", 18)
    except OSError:
        font_lg = ImageFont.load_default()
        font_md = font_lg
        font_sm = font_lg
    
    # Icon text (emoji or symbol)
    bbox = draw.textbbox((0, 0), icon_text, font=font_lg)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((icon_cx - tw // 2, icon_cy - th // 2 - 5), icon_text, fill=(255, 255, 255), font=font_lg)
    
    # Title
    draw.text((W // 2, card_top + 160), title, fill=SAELAR_DARK, font=font_md, anchor="mt")
    
    # Subtitle
    draw.text((W // 2, card_top + 200), "SAELAR", fill=(100, 116, 139), font=font_sm, anchor="mt")
    
    OUTPUT.mkdir(parents=True, exist_ok=True)
    out = OUTPUT / "saelar" / filename
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    return out


# SOPRA brand colors (cyan/teal)
SOPRA_CYAN = (0, 217, 255)
SOPRA_DARK = (14, 25, 45)


def create_sopra_card(title, icon_text, filename):
    """Create a branded card for SOPRA slides."""
    img = create_gradient_bg(W, H)
    draw = ImageDraw.Draw(img)
    
    # SOPRA accent (cyan)
    draw.rectangle([0, 0, W, 8], fill=SOPRA_CYAN)
    
    margin = 40
    card_top, card_left = 60, margin
    card_w, card_h = W - 2 * margin, H - 120
    draw.rounded_rectangle([card_left, card_top, card_left + card_w, card_top + card_h],
                          radius=16, fill=(255, 255, 255), outline=SOPRA_CYAN, width=2)
    
    icon_cx, icon_cy = W // 2, card_top + 80
    draw.ellipse([icon_cx - 60, icon_cy - 60, icon_cx + 60, icon_cy + 60],
                 fill=SOPRA_DARK, outline=SOPRA_CYAN, width=2)
    
    try:
        font_lg = ImageFont.truetype("arial.ttf", 48)
        font_md = ImageFont.truetype("arial.ttf", 28)
        font_sm = ImageFont.truetype("arial.ttf", 18)
    except OSError:
        font_lg = ImageFont.load_default()
        font_md = font_lg
        font_sm = font_lg
    
    bbox = draw.textbbox((0, 0), icon_text, font=font_lg)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((icon_cx - tw // 2, icon_cy - th // 2 - 5), icon_text, fill=SOPRA_CYAN, font=font_lg)
    
    draw.text((W // 2, card_top + 160), title, fill=SOPRA_DARK, font=font_md, anchor="mt")
    draw.text((W // 2, card_top + 200), "SOPRA", fill=(100, 116, 139), font=font_sm, anchor="mt")
    
    out = OUTPUT / "sopra" / filename
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    return out


def main():
    cards = [
        ("01_what_is.png", "What is SAELAR?", "🛡️"),
        ("02_getting_started.png", "Getting Started", "🚀"),
        ("03_main_tabs.png", "Main Tabs", "📑"),
        ("04_nist_assessment.png", "NIST Assessment", "📋"),
        ("05_chad.png", "Chad AI Assistant", "🤖"),
        ("06_ssp_poam.png", "SSP & POA&Ms", "📄"),
        ("07_bod_kev.png", "BOD 22-01 (KEV)", "🚨"),
        ("08_tips.png", "Tips for ISSOs", "💡"),
        ("09_need_help.png", "Need Help?", "❓"),
    ]
    print("SAELAR graphics:")
    for fname, title, icon in cards:
        create_saelar_card(title, icon, fname)
        print(f"  {fname}")
    
    sopra_cards = [
        ("01_what_is.png", "What is SOPRA?", "🛡️"),
        ("02_getting_started.png", "Getting Started", "🚀"),
        ("03_main_sections.png", "Main Sections", "📑"),
        ("04_assessment.png", "Assessment Workflow", "📋"),
        ("05_dashboard.png", "Dashboard Metrics", "📊"),
        ("06_isso_toolkit.png", "ISSO Toolkit", "🔧"),
        ("07_vuln_mgmt.png", "Vulnerability Management", "🧠"),
        ("08_ssp_reports.png", "SSP & Reports", "📄"),
        ("09_tips.png", "Tips for ISSOs", "💡"),
        ("10_need_help.png", "Need Help?", "❓"),
    ]
    print("SOPRA graphics:")
    for fname, title, icon in sopra_cards:
        create_sopra_card(title, icon, fname)
        print(f"  {fname}")


if __name__ == "__main__":
    main()
