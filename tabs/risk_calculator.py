"""Risk Calculator tab – compute and visualize risk scores."""

import streamlit as st
import pandas as pd

LIKELIHOOD_SCALE = {"Very Low": 1, "Low": 2, "Moderate": 3, "High": 4, "Very High": 5}
IMPACT_SCALE = {"Very Low": 1, "Low": 2, "Moderate": 3, "High": 4, "Very High": 5}

RISK_THRESHOLDS = {
    (1, 6): ("Low", "🟢"),
    (7, 12): ("Moderate", "🟡"),
    (13, 19): ("High", "🟠"),
    (20, 25): ("Critical", "🔴"),
}


def _risk_label(score: int) -> tuple[str, str]:
    for (lo, hi), (label, icon) in RISK_THRESHOLDS.items():
        if lo <= score <= hi:
            return label, icon
    return "Unknown", "⚪"


def _init_state():
    if "risk_items" not in st.session_state:
        st.session_state.risk_items = []


def render_risk_calculator():
    _init_state()
    st.header("Risk Calculator")
    st.markdown(
        "Evaluate organizational risks by specifying likelihood and impact for "
        "each identified threat. The calculator produces a risk score and overall "
        "risk posture summary."
    )

    _render_add_risk()
    st.divider()
    _render_risk_table()
    st.divider()
    _render_risk_matrix()


def _render_add_risk():
    st.subheader("Add Risk Item")
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        threat = st.text_input("Threat / Vulnerability", key="risk_threat")
    with col2:
        likelihood = st.selectbox(
            "Likelihood", list(LIKELIHOOD_SCALE.keys()), key="risk_likelihood"
        )
    with col3:
        impact = st.selectbox(
            "Impact", list(IMPACT_SCALE.keys()), key="risk_impact"
        )

    mitigation = st.text_area("Planned Mitigation", key="risk_mitigation", height=80)

    if st.button("Add Risk", key="risk_add"):
        if not threat:
            st.warning("Please describe the threat or vulnerability.")
        else:
            score = LIKELIHOOD_SCALE[likelihood] * IMPACT_SCALE[impact]
            label, icon = _risk_label(score)
            st.session_state.risk_items.append({
                "Threat": threat,
                "Likelihood": likelihood,
                "Impact": impact,
                "Score": score,
                "Level": f"{icon} {label}",
                "Mitigation": mitigation,
            })
            st.success(f"Added risk: {threat} (Score: {score} – {label})")


def _render_risk_table():
    st.subheader("Risk Register")
    items = st.session_state.risk_items
    if not items:
        st.info("No risk items yet. Add one above.")
        return

    df = pd.DataFrame(items)
    st.dataframe(df, use_container_width=True, hide_index=True)

    avg_score = df["Score"].mean()
    label, icon = _risk_label(int(round(avg_score)))
    st.metric("Average Risk Score", f"{avg_score:.1f}", f"{icon} {label}")

    if st.button("Clear All Risks", key="risk_clear"):
        st.session_state.risk_items = []
        st.rerun()


def _render_risk_matrix():
    st.subheader("5 × 5 Risk Matrix")

    matrix_data = [[0] * 5 for _ in range(5)]
    for item in st.session_state.risk_items:
        l_idx = LIKELIHOOD_SCALE[item["Likelihood"]] - 1
        i_idx = IMPACT_SCALE[item["Impact"]] - 1
        matrix_data[l_idx][i_idx] += 1

    impact_labels = list(IMPACT_SCALE.keys())
    likelihood_labels = list(LIKELIHOOD_SCALE.keys())

    df_matrix = pd.DataFrame(
        matrix_data,
        index=likelihood_labels,
        columns=impact_labels,
    )
    df_matrix.index.name = "Likelihood ↓ / Impact →"

    try:
        styled = df_matrix.style.background_gradient(cmap="YlOrRd", vmin=0)
        st.dataframe(styled, use_container_width=True)
    except Exception:
        st.dataframe(df_matrix, use_container_width=True)
