"""SOPRA Continuous Monitoring — US-CERT / CISA Inspired Design"""
import streamlit as st
import os
import base64
from datetime import datetime

from sopra.persistence import load_assessment_history, load_results_from_file, _append_to_history


def _load_logo_b64():
    """Load the SOPRA logo as a base64-encoded string."""
    _root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    for name in ("SOPRA_logo_dark.png", "OPRA_logo_dark.png"):
        p = os.path.join(_root, "assets", name)
        if os.path.exists(p):
            with open(p, "rb") as f:
                return base64.b64encode(f.read()).decode()
    return None


def render_conmon_page():
    """Continuous Monitoring dashboard styled after CISA.gov advisory pages."""

    # ── Global Styling ───────────────────────────────────────────────
    st.markdown("""
    <style>
        section[data-testid="stSidebar"] { display: none !important; }
        [data-testid="stSidebarCollapsedControl"] { display: none !important; }
        header[data-testid="stHeader"] { background: transparent !important; }
        [data-testid="stAppViewContainer"], .stApp {
            background: #0b1120 !important;
        }
        [data-testid="stAppViewContainer"] p,
        [data-testid="stAppViewContainer"] span,
        [data-testid="stAppViewContainer"] li,
        [data-testid="stAppViewContainer"] td,
        [data-testid="stAppViewContainer"] th,
        [data-testid="stAppViewContainer"] label,
        [data-testid="stAppViewContainer"] h1,
        [data-testid="stAppViewContainer"] h2,
        [data-testid="stAppViewContainer"] h3,
        [data-testid="stAppViewContainer"] h4 { color: #d8e2ef !important; }
        [data-testid="stMetricValue"] { color: #00d9ff !important; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #0b1120; }
        ::-webkit-scrollbar-thumb { background: #1e3a5f; border-radius: 3px; }
    </style>
    """, unsafe_allow_html=True)

    # ── Load Data ────────────────────────────────────────────────────
    history = load_assessment_history()
    current = load_results_from_file()

    if not history or len(history) < 1:
        if current and current.get("findings"):
            _append_to_history(current)
            history = load_assessment_history()
        if not history:
            _render_empty_state()
            return

    latest = history[-1]
    prev = history[-2] if len(history) >= 2 else None
    _now = datetime.now().strftime('%Y-%m-%d %H:%M')

    comp_pct = latest.get("compliance_pct", 0)
    comp_delta = round(comp_pct - prev.get("compliance_pct", comp_pct), 1) if prev else 0
    fail_count = latest.get("failed", 0)
    passed_count = latest.get("passed", 0)
    total = passed_count + fail_count
    sev_counts = latest.get("severity_counts", {})
    crit = sev_counts.get("Critical", 0)
    high = sev_counts.get("High", 0)

    # ── Determine Threat Level ───────────────────────────────────────
    if crit > 5 or comp_pct < 40:
        threat_level, threat_color, threat_bg = "SEVERE", "#ff1744", "rgba(255,23,68,0.12)"
    elif crit > 0 or comp_pct < 60:
        threat_level, threat_color, threat_bg = "HIGH", "#e94560", "rgba(233,69,96,0.10)"
    elif high > 5 or comp_pct < 75:
        threat_level, threat_color, threat_bg = "ELEVATED", "#ff9800", "rgba(255,152,0,0.10)"
    elif comp_pct < 90:
        threat_level, threat_color, threat_bg = "GUARDED", "#ffc107", "rgba(255,193,7,0.10)"
    else:
        threat_level, threat_color, threat_bg = "LOW", "#00e676", "rgba(0,230,118,0.10)"

    # ── Top Banner (CISA-style with logo) ────────────────────────────
    logo_b64 = _load_logo_b64()
    if logo_b64:
        logo_tag = '<img src="data:image/png;base64,' + logo_b64 + '" style="height:160px;filter:drop-shadow(0 0 12px rgba(0,217,255,0.45));" alt="SOPRA">'
    else:
        logo_tag = '<span style="font-size:3rem;font-weight:900;color:#00d9ff;">🛡️ SOPRA</span>'

    st.markdown(
        '<div style="display:flex;align-items:center;gap:1.5rem;padding:0.8rem 0;margin-bottom:0.3rem;">'
        '<div style="flex-shrink:0;">' + logo_tag + '</div>'
        '<div style="flex:1;">'
        '<div style="font-size:3.4rem;font-weight:900;color:#ffffff;letter-spacing:1px;line-height:1.1;">Continuous Monitoring</div>'
        '<div style="font-size:1.1rem;color:#5a7a9a;margin-top:0.3rem;letter-spacing:1px;">Security Posture Tracking</div>'
        '</div>'
        '<div style="flex-shrink:0;text-align:right;">'
        '<div style="font-size:0.75rem;color:#4a6a8a;">Last Updated: ' + _now + '</div>'
        '</div>'
        '</div>'
        '<div style="border-bottom:3px solid #1b3a5c;margin-bottom:1rem;"></div>',
        unsafe_allow_html=True
    )

    # ── Threat Level Banner ──────────────────────────────────────────
    st.markdown('<div style="height:0.8rem;"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="background:' + threat_bg + ';border:2px solid ' + threat_color + ';border-radius:8px;padding:1.2rem 1.5rem;margin-bottom:1.2rem;">'
        '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem;">'
        '<div>'
        '<div style="font-size:0.7rem;letter-spacing:3px;color:#7a8a9a;text-transform:uppercase;margin-bottom:0.3rem;">Current Security Posture</div>'
        '<div style="font-size:2.2rem;font-weight:900;color:' + threat_color + ';line-height:1;">' + threat_level + '</div>'
        '</div>'
        '<div style="display:flex;gap:2rem;align-items:center;">'
        '<div style="text-align:center;">'
        '<div style="font-size:2.5rem;font-weight:800;color:#fff;">' + str(comp_pct) + '%</div>'
        '<div style="font-size:0.85rem;color:#7a8a9a;">Compliance Rate</div></div>'
        '<div style="text-align:center;">'
        '<div style="font-size:2.5rem;font-weight:800;color:#e94560;">' + str(fail_count) + '</div>'
        '<div style="font-size:0.85rem;color:#7a8a9a;">Failed Controls</div></div>'
        '<div style="text-align:center;">'
        '<div style="font-size:2.5rem;font-weight:800;color:#00e676;">' + str(passed_count) + '</div>'
        '<div style="font-size:0.85rem;color:#7a8a9a;">Passed Controls</div></div>'
        '</div></div></div>',
        unsafe_allow_html=True
    )

    # ── Severity Summary Bar ─────────────────────────────────────────
    st.markdown(
        '<div style="display:flex;gap:0.5rem;margin-bottom:1.5rem;">'
        + _sev_pill("CRITICAL", crit, "#ff1744")
        + _sev_pill("HIGH", high, "#e94560")
        + _sev_pill("MEDIUM", sev_counts.get("Medium", 0), "#ff9800")
        + _sev_pill("LOW", sev_counts.get("Low", 0), "#2196f3")
        + '</div>',
        unsafe_allow_html=True
    )

    # ── Two-Column Layout ────────────────────────────────────────────
    col_left, col_right = st.columns([3, 2])

    with col_left:
        # ── Category Advisories ──────────────────────────────────────
        st.markdown(
            '<div style="font-size:1.1rem;font-weight:700;color:#fff;margin-bottom:0.8rem;padding-bottom:0.4rem;border-bottom:2px solid #1b3a5c;">'
            'Category Compliance Status</div>',
            unsafe_allow_html=True
        )

        cat_scores = latest.get("category_scores", {})
        prev_scores = prev.get("category_scores", {}) if prev else {}

        # Sort: worst compliance first
        sorted_cats = sorted(cat_scores.items(), key=lambda x: x[1])

        for cat, score in sorted_cats:
            prev_score = prev_scores.get(cat, score)
            delta = score - prev_score

            if score >= 80:
                status, s_color, s_bg = "COMPLIANT", "#00e676", "rgba(0,230,118,0.08)"
            elif score >= 50:
                status, s_color, s_bg = "AT RISK", "#ff9800", "rgba(255,152,0,0.08)"
            else:
                status, s_color, s_bg = "NON-COMPLIANT", "#ff1744", "rgba(255,23,68,0.08)"

            if delta > 0:
                d_text = '<span style="color:#00e676;font-size:0.85rem;">&#9650; +' + str(abs(delta)) + '%</span>'
            elif delta < 0:
                d_text = '<span style="color:#ff1744;font-size:0.85rem;">&#9660; -' + str(abs(delta)) + '%</span>'
            else:
                d_text = '<span style="color:#546e7a;font-size:0.85rem;">&#8212; No change</span>'

            st.markdown(
                '<div style="background:' + s_bg + ';border:1px solid ' + s_color + '30;border-left:4px solid ' + s_color + ';border-radius:6px;padding:0.8rem 1rem;margin-bottom:0.5rem;">'
                '<div style="display:flex;justify-content:space-between;align-items:center;">'
                '<div>'
                '<div style="font-size:1rem;font-weight:700;color:#e0e8f0;">' + cat + '</div>'
                '<div style="margin-top:0.2rem;">' + d_text + '</div>'
                '</div>'
                '<div style="text-align:right;">'
                '<div style="font-size:1.5rem;font-weight:800;color:' + s_color + ';">' + str(score) + '%</div>'
                '<div style="font-size:0.7rem;letter-spacing:1px;color:' + s_color + ';font-weight:700;">' + status + '</div>'
                '</div></div>'
                '<div style="background:rgba(255,255,255,0.06);border-radius:4px;height:6px;margin-top:0.5rem;overflow:hidden;">'
                '<div style="width:' + str(score) + '%;height:100%;background:' + s_color + ';border-radius:4px;"></div></div>'
                '</div>',
                unsafe_allow_html=True
            )

    with col_right:
        # ── Assessment Timeline (advisory feed) ──────────────────────
        st.markdown(
            '<div style="font-size:1.1rem;font-weight:700;color:#fff;margin-bottom:0.8rem;padding-bottom:0.4rem;border-bottom:2px solid #1b3a5c;">'
            'Assessment Timeline</div>',
            unsafe_allow_html=True
        )

        for h in reversed(history[-10:]):
            ts = h.get("timestamp", "")[:16].replace("T", " ")
            cpct = h.get("compliance_pct", 0)
            p = h.get("passed", 0)
            f = h.get("failed", 0)
            src = h.get("source", "Assessment")

            if cpct >= 80:
                a_color = "#00e676"
            elif cpct >= 50:
                a_color = "#ff9800"
            else:
                a_color = "#ff1744"

            st.markdown(
                '<div style="border-left:3px solid ' + a_color + ';padding:0.6rem 0.8rem;margin-bottom:0.6rem;background:rgba(13,27,42,0.6);border-radius:0 6px 6px 0;">'
                '<div style="display:flex;justify-content:space-between;align-items:baseline;">'
                '<div style="font-size:0.8rem;color:#5a7a9a;">' + ts + '</div>'
                '<div style="font-size:1.3rem;font-weight:800;color:' + a_color + ';">' + str(cpct) + '%</div>'
                '</div>'
                '<div style="font-size:0.9rem;color:#c0d0e0;margin-top:0.2rem;">' + src + '</div>'
                '<div style="font-size:0.8rem;color:#5a7a9a;margin-top:0.15rem;">'
                '<span style="color:#00e676;">' + str(p) + ' passed</span> &nbsp;&bull;&nbsp; '
                '<span style="color:#e94560;">' + str(f) + ' failed</span></div>'
                '</div>',
                unsafe_allow_html=True
            )

        # ── Findings Requiring Action ────────────────────────────────
        st.markdown(
            '<div style="font-size:1.1rem;font-weight:700;color:#fff;margin:1.2rem 0 0.8rem;padding-bottom:0.4rem;border-bottom:2px solid #1b3a5c;">'
            'Findings Requiring Action</div>',
            unsafe_allow_html=True
        )

        results = load_results_from_file()
        if results and results.get("findings"):
            failed_findings = [f for f in results["findings"] if f["status"] == "Failed"]
            # Group by severity
            by_sev = {"Critical": [], "High": [], "Medium": [], "Low": []}
            for f in failed_findings:
                sev = f.get("severity", "Medium")
                if sev in by_sev:
                    by_sev[sev].append(f)

            sev_styles = {
                "Critical": ("#ff1744", "&#9888;"),
                "High": ("#e94560", "&#9679;"),
                "Medium": ("#ff9800", "&#9679;"),
                "Low": ("#2196f3", "&#9679;"),
            }

            shown = 0
            for sev in ["Critical", "High", "Medium", "Low"]:
                items = by_sev.get(sev, [])
                if not items:
                    continue
                color, icon = sev_styles[sev]
                for f in items[:3]:
                    st.markdown(
                        '<div style="padding:0.4rem 0.6rem;margin-bottom:0.3rem;border-left:3px solid ' + color + ';background:rgba(13,27,42,0.4);border-radius:0 4px 4px 0;">'
                        '<div style="display:flex;align-items:center;gap:0.5rem;">'
                        '<span style="color:' + color + ';font-size:0.85rem;font-weight:700;">' + icon + ' ' + sev.upper() + '</span>'
                        '<span style="color:#b0c4de;font-size:0.85rem;">' + f.get("control_id", "") + '</span>'
                        '</div>'
                        '<div style="font-size:0.8rem;color:#7a8a9a;margin-top:0.1rem;">' + f.get("control_name", "")[:60] + '</div>'
                        '</div>',
                        unsafe_allow_html=True
                    )
                    shown += 1
                if shown >= 12:
                    break

            remaining = len(failed_findings) - shown
            if remaining > 0:
                st.markdown(
                    '<div style="text-align:center;padding:0.4rem;color:#5a7a9a;font-size:0.8rem;">+ ' + str(remaining) + ' more findings</div>',
                    unsafe_allow_html=True
                )
        else:
            st.markdown(
                '<div style="color:#5a7a9a;font-size:0.9rem;padding:0.5rem;">No assessment data loaded.</div>',
                unsafe_allow_html=True
            )

    # ── Trend Change Summary (bottom) ────────────────────────────────
    if prev:
        st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:1.1rem;font-weight:700;color:#fff;margin-bottom:0.8rem;padding-bottom:0.4rem;border-bottom:2px solid #1b3a5c;">'
            'Change Summary — Current vs. Previous Assessment</div>',
            unsafe_allow_html=True
        )

        changes = []
        prev_comp = prev.get("compliance_pct", 0)
        prev_fail = prev.get("failed", 0)
        prev_pass = prev.get("passed", 0)

        if comp_delta > 0:
            changes.append(("Compliance improved by " + str(abs(comp_delta)) + "% (from " + str(prev_comp) + "% to " + str(comp_pct) + "%)", "#00e676", "&#9650;"))
        elif comp_delta < 0:
            changes.append(("Compliance decreased by " + str(abs(comp_delta)) + "% (from " + str(prev_comp) + "% to " + str(comp_pct) + "%)", "#ff1744", "&#9660;"))

        fail_delta = fail_count - prev_fail
        if fail_delta > 0:
            changes.append((str(abs(fail_delta)) + " new failed controls detected", "#ff1744", "&#9660;"))
        elif fail_delta < 0:
            changes.append((str(abs(fail_delta)) + " previously failed controls now passing", "#00e676", "&#9650;"))

        # Check for severity changes
        prev_sev = prev.get("severity_counts", {})
        for sev in ["Critical", "High"]:
            curr_val = sev_counts.get(sev, 0)
            prev_val = prev_sev.get(sev, 0)
            d = curr_val - prev_val
            if d > 0:
                changes.append((str(d) + " new " + sev + " severity finding(s)", "#ff1744", "&#9888;"))
            elif d < 0:
                changes.append((str(abs(d)) + " " + sev + " finding(s) resolved", "#00e676", "&#10003;"))

        # Category regressions
        cat_scores_now = latest.get("category_scores", {})
        cat_scores_prev = prev.get("category_scores", {})
        regressed = []
        improved = []
        for cat in cat_scores_now:
            d = cat_scores_now.get(cat, 0) - cat_scores_prev.get(cat, 0)
            if d < -10:
                regressed.append(cat)
            elif d > 10:
                improved.append(cat)
        if regressed:
            changes.append((", ".join(regressed) + " — significant regression (>10%)", "#ff9800", "&#9888;"))
        if improved:
            changes.append((", ".join(improved) + " — significant improvement (>10%)", "#00e676", "&#10003;"))

        if not changes:
            changes.append(("No significant changes detected between assessments", "#546e7a", "&#8212;"))

        for text, color, icon in changes:
            st.markdown(
                '<div style="display:flex;align-items:center;gap:0.6rem;padding:0.6rem 0.8rem;margin-bottom:0.35rem;background:rgba(13,27,42,0.5);border-left:3px solid ' + color + ';border-radius:0 6px 6px 0;">'
                '<span style="color:' + color + ';font-size:1.1rem;">' + icon + '</span>'
                '<span style="font-size:0.95rem;color:#c0d0e0;">' + text + '</span>'
                '</div>',
                unsafe_allow_html=True
            )

    # ── Footer ───────────────────────────────────────────────────────
    st.markdown(
        '<div style="margin-top:2rem;padding:0.8rem 1rem;border-top:1px solid #1b3a5c;text-align:center;">'
        '<div style="font-size:0.75rem;color:#3a5a7a;">SOPRA Continuous Monitoring &bull; NIST SP 800-137 ISCM &bull; Generated ' + _now + '</div>'
        '</div>',
        unsafe_allow_html=True
    )


def _sev_pill(label, count, color):
    """Generate a severity pill HTML fragment."""
    return (
        '<div style="flex:1;text-align:center;padding:0.7rem 0.5rem;background:rgba(13,27,42,0.7);'
        'border:1px solid ' + color + '40;border-radius:8px;">'
        '<div style="font-size:1.8rem;font-weight:800;color:' + color + ';">' + str(count) + '</div>'
        '<div style="font-size:0.7rem;letter-spacing:2px;color:' + color + ';font-weight:600;">' + label + '</div>'
        '</div>'
    )


def _render_empty_state():
    """Show empty state when no assessment history exists."""
    st.markdown(
        '<div style="text-align:center;padding:4rem 2rem;">'
        '<div style="font-size:3rem;margin-bottom:1rem;">🛡️</div>'
        '<div style="font-size:1.5rem;font-weight:700;color:#fff;margin-bottom:0.5rem;">No Assessment Data Available</div>'
        '<div style="font-size:1rem;color:#5a7a9a;max-width:500px;margin:0 auto;">Run at least one security assessment from the SOPRA dashboard to begin continuous monitoring. Assessment history will populate automatically.</div>'
        '</div>',
        unsafe_allow_html=True
    )
