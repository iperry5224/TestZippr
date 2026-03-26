"""SOPRA ISSO — Assessment Scheduling & Recurrence (AI-Enhanced)"""
import streamlit as st
from datetime import datetime
import datetime as dt_module

from sopra.persistence import _load_json, _save_json, _next_id, load_results_from_file
from sopra.isso.ai_engine import ai_recommend_schedule

def render_assessment_scheduling():
    """Set assessment schedules with recurrence, reminders, and AI frequency recommendations."""
    st.markdown("## 📅 Assessment Scheduling & Recurrence")
    st.markdown("Define reassessment cadence for each control category. Continuous monitoring requires periodic reassessment.")

    schedules = _load_json("assessment_schedules.json", [])
    results = st.session_state.get("opra_assessment_results")
    if not results or not results.get("findings"):
        results = load_results_from_file()
        if results:
            st.session_state.opra_assessment_results = results

    categories = set()
    if results and results.get("findings"):
        for f in results["findings"]:
            categories.add(f.get("category", "Unknown"))
    categories = sorted(categories) if categories else ["Active Directory", "Network Infrastructure", "Endpoint Security", "Server Security", "Identity & Access Management", "Data Protection", "Monitoring & Logging", "Physical Security"]

    # Auto-init schedules if empty
    if not schedules:
        for cat in categories:
            schedules.append({
                "id": _next_id(schedules, "SCHED"),
                "category": cat,
                "frequency_days": 90,
                "last_assessed": datetime.now().strftime("%Y-%m-%d"),
                "assigned_to": "TBD",
                "status": "On Schedule"
            })
        _save_json("assessment_schedules.json", schedules)

    today = datetime.now().strftime("%Y-%m-%d")
    today_dt = datetime.now()

    # Update statuses
    for s in schedules:
        try:
            last_dt = datetime.strptime(s["last_assessed"], "%Y-%m-%d")
            next_dt = last_dt + __import__('datetime').timedelta(days=s["frequency_days"])
            s["next_due"] = next_dt.strftime("%Y-%m-%d")
            days_left = (next_dt - today_dt).days
            if days_left < 0:
                s["status"] = "Overdue"
            elif days_left <= 14:
                s["status"] = "Due Soon"
            else:
                s["status"] = "On Schedule"
        except Exception:
            s["next_due"] = "N/A"
            s["status"] = "Unknown"
    _save_json("assessment_schedules.json", schedules)

    # KPIs
    overdue = len([s for s in schedules if s["status"] == "Overdue"])
    due_soon = len([s for s in schedules if s["status"] == "Due Soon"])
    on_sched = len([s for s in schedules if s["status"] == "On Schedule"])
    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric("On Schedule", on_sched)
    with k2:
        st.metric("Due Soon (<=14 days)", due_soon, delta=f"! {due_soon}" if due_soon else "0")
    with k3:
        st.metric("Overdue", overdue, delta=f"-{overdue}" if overdue else "0", delta_color="inverse")

    # ── AI Schedule Optimization ─────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🤖 AI Schedule Optimization")
    st.caption("AI analyzes failure rates and severity profiles to recommend optimal assessment frequencies based on NIST SP 800-137 ISCM guidance.")

    if st.button("🤖 AI Optimize All Schedules", type="primary", key="sched_ai_optimize"):
        findings = results.get("findings", []) if results else []
        recommendations = []

        with st.spinner("AI is analyzing risk profiles and recommending frequencies..."):
            for s in schedules:
                cat = s["category"]
                # Calculate failure rate for this category
                cat_findings = [f for f in findings if f.get("category") == cat]
                total = len(cat_findings)
                failed = len([f for f in cat_findings if f["status"] == "Failed"])
                failure_rate = round(failed / max(total, 1) * 100)
                severities = [f.get("severity", "Medium") for f in cat_findings if f["status"] == "Failed"]
                sev_profile = ", ".join(set(severities)) if severities else "No failures"

                rec = ai_recommend_schedule(cat, s["frequency_days"], failure_rate, sev_profile)
                recommendations.append({"schedule": s, "recommendation": rec, "failure_rate": failure_rate})

        for rec in recommendations:
            s = rec["schedule"]
            with st.expander(f"📂 {s['category']} — Current: {s['frequency_days']}d | Failure Rate: {rec['failure_rate']}%"):
                st.markdown(rec["recommendation"])

                # Try to extract recommended frequency from AI text
                import re
                freq_match = re.search(r'(\d+)\s*days?', rec["recommendation"])
                if freq_match:
                    suggested_freq = int(freq_match.group(1))
                    if suggested_freq != s["frequency_days"]:
                        if st.button(f"Apply {suggested_freq}-day schedule", key=f"sched_apply_{s['id']}"):
                            s["frequency_days"] = suggested_freq
                            _save_json("assessment_schedules.json", schedules)
                            st.success(f"Updated {s['category']} to {suggested_freq}-day frequency.")
                            st.rerun()

    st.markdown("---")

    for s in schedules:
        status_color = {"On Schedule": "#00ff88", "Due Soon": "#ffc107", "Overdue": "#e94560"}.get(s["status"], "#888")
        alert = " 🚨" if s["status"] == "Overdue" else (" ⚠️" if s["status"] == "Due Soon" else "")

        with st.expander(f"📂 {s['category']} — {s['status']}{alert}"):
            st.markdown(f"<span style='color:{status_color};font-weight:700;font-size:1rem;'>{s['status']}</span>", unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            with c1:
                new_freq = st.number_input("Frequency (days)", min_value=7, max_value=365, value=s["frequency_days"], key=f"sched_freq_{s['id']}")
            with c2:
                new_assigned = st.text_input("Assigned To", value=s.get("assigned_to", "TBD"), key=f"sched_assign_{s['id']}")
            with c3:
                st.markdown(f"**Next Due:** {s.get('next_due', 'N/A')}")
                st.markdown(f"**Last Assessed:** {s['last_assessed']}")

            c_a, c_b = st.columns(2)
            with c_a:
                if st.button("💾 Update Schedule", key=f"sched_save_{s['id']}"):
                    s["frequency_days"] = new_freq
                    s["assigned_to"] = new_assigned
                    _save_json("assessment_schedules.json", schedules)
                    st.success("Schedule updated.")
                    st.rerun()
            with c_b:
                if st.button("✅ Mark Assessed Today", key=f"sched_mark_{s['id']}"):
                    s["last_assessed"] = today
                    _save_json("assessment_schedules.json", schedules)
                    st.success(f"Marked {s['category']} as assessed today.")
                    st.rerun()
