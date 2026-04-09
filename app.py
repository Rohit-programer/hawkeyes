"""
AI Future Simulator - Streamlit Frontend
Run with: streamlit run app.py
"""

import streamlit as st
import requests
import json
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ─── Config ──────────────────────────────────────────────────
BACKEND_URL = "http://localhost:8000"

st.set_page_config(
    page_title="AI Decision Simulator",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ──────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0a0a0f; }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; border: none; border-radius: 12px;
        padding: 0.75rem 2rem; font-size: 1.1rem; font-weight: 600;
        width: 100%; transition: all 0.3s ease;
    }
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #30305a; border-radius: 16px;
        padding: 1.5rem; text-align: center; margin-bottom: 1rem;
    }
    .risk-high   { color: #ff6b6b; font-weight: bold; }
    .risk-medium { color: #ffd93d; font-weight: bold; }
    .risk-low    { color: #6bcb77; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ─── Header ──────────────────────────────────────────────────
st.markdown("# 🔮 AI Future Simulator")
st.markdown("*Simulate the long-term impact of your decisions before you make them.*")
st.divider()

# ─── Layout ──────────────────────────────────────────────────
left_col, right_col = st.columns([1, 2], gap="large")

# ────────────────────────── LEFT: INPUTS ─────────────────────
with left_col:
    st.subheader("📝 Your Decision")

    decision = st.text_area(
        "What decision are you considering?",
        placeholder="e.g. Start a gadget company in AI tooling targeting SMEs",
        height=100
    )

    category = st.selectbox(
        "Category",
        ["Business / Startup", "Career Change", "Investment", "Education", "Real Estate", "Personal Life", "Other"]
    )

    budget = st.number_input(
        "Available Budget (RS )",
        min_value=0.0,
        max_value=10_000_000.0,
        value=50_000.0,
        step=5_000.0,
        format="%.2f"
    )

    duration = st.slider("Simulation Horizon (years)", min_value=1, max_value=10, value=3)

    risk_level = st.select_slider(
        "Risk Appetite",
        options=["low", "medium", "high"],
        value="medium"
    )

    st.divider()

    simulate_btn = st.button("🚀 Simulate My Future", use_container_width=True)

    # ── What-If Comparison ──
    st.subheader("🔄 What-If Comparison")
    st.caption("Change one variable and compare outcomes side by side")

    compare_budget = st.number_input(
        "Alternative Budget ($)",
        value=budget * 2,
        step=5_000.0,
        format="%.2f"
    )
    compare_risk = st.select_slider(
        "Alternative Risk",
        options=["low", "medium", "high"],
        value="high"
    )
    compare_btn = st.button("⚡ Run Comparison", use_container_width=True)

    # ── History ──
    st.subheader("📂 Past Simulations")
    if st.button("Load History", use_container_width=True):
        try:
            resp = requests.get(f"{BACKEND_URL}/simulations", timeout=10)
            history = resp.json()
            for h in history[:5]:
                st.markdown(f"**#{h['id']}** {h['decision'][:40]}... `{h['risk_level']}` _{h['created_at'][:10]}_")
        except Exception as e:
            st.error(f"Backend not reachable: {e}")


# ─── Helper: Render Results ──────────────────────────────────
def render_results(data: dict, label: str = ""):
    r = data.get("result", {})
    if not r:
        st.error("Empty result from AI. Try again.")
        return

    if label:
        st.subheader(f"Results — {label}")

    # ── KPI Cards ──
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    fin = r.get("financial_outcome", {})

    kpi1.metric("✅ Success Probability", f"{r.get('success_probability', 0)}%")
    kpi2.metric("💵 Projected Return", f"${fin.get('projected_return', 0):,.0f}")
    kpi3.metric("📈 ROI", f"{fin.get('roi_percent', 0):.1f}%")
    kpi4.metric("⏱ Break-even", f"{fin.get('break_even_months', 0)} months")

    st.info(r.get("summary", ""))

    tab_timeline, tab_risks, tab_opps, tab_alts = st.tabs(
        ["📅 Timeline", "⚠️ Risks", "💡 Opportunities", "🛤 Alternatives"]
    )

    # ── Timeline Chart ──
    with tab_timeline:
        timeline = r.get("yearly_timeline", [])
        if timeline:
            df = pd.DataFrame(timeline)
            fig = px.bar(
                df, x="year", y="financial_position",
                text="milestone", color="financial_position",
                color_continuous_scale="Viridis",
                labels={"financial_position": "Financial Position ($)", "year": "Year"},
                title="Projected Financial Position Year by Year"
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(template="plotly_dark", height=350)
            st.plotly_chart(fig, use_container_width=True)

            for yr in timeline:
                with st.expander(f"Year {yr['year']}: {yr['title']}"):
                    st.write(yr["description"])
                    st.caption(f"🏆 Milestone: {yr['milestone']}")

    # ── Risks ──
    with tab_risks:
        risks = r.get("risks", [])
        if risks:
            risk_df = pd.DataFrame(risks)
            fig = px.scatter(
                risk_df, x="probability_percent", y="risk",
                size=[30]*len(risks), color="severity",
                color_discrete_map={"high": "#ff6b6b", "medium": "#ffd93d", "low": "#6bcb77"},
                title="Risk Map"
            )
            fig.update_layout(template="plotly_dark", height=300)
            st.plotly_chart(fig, use_container_width=True)

            for risk in risks:
                sev = risk["severity"]
                color = "🔴" if sev == "high" else "🟡" if sev == "medium" else "🟢"
                with st.expander(f"{color} {risk['risk']} ({risk['probability_percent']}% probability)"):
                    st.write(f"**Mitigation:** {risk['mitigation']}")

    # ── Opportunities ──
    with tab_opps:
        opps = r.get("opportunities", [])
        for opp in opps:
            imp = opp["impact"]
            icon = "🔥" if imp == "high" else "⚡" if imp == "medium" else "💧"
            with st.expander(f"{icon} {opp['opportunity']} — {imp} impact"):
                st.write(f"**Action:** {opp['action']}")

        st.success(f"💡 **Top Recommendation:** {r.get('recommendation', '')}")

    # ── Alternatives ──
    with tab_alts:
        alts = r.get("alternative_paths", [])
        if alts:
            alt_df = pd.DataFrame(alts)
            fig = px.bar(
                alt_df, x="path", y="success_probability",
                color="success_probability",
                color_continuous_scale="RdYlGn",
                title="Alternative Paths — Success Probability",
                labels={"success_probability": "Success %", "path": "Approach"}
            )
            fig.update_layout(template="plotly_dark", height=300)
            st.plotly_chart(fig, use_container_width=True)

            for alt in alts:
                st.markdown(f"**{alt['path']}** ({alt['success_probability']}%) — {alt['description']}")


# ─── RIGHT SIDE: Results ─────────────────────────────────────
with right_col:

    # ── Main Simulation ──
    if simulate_btn:
        if not decision.strip():
            st.warning("Please describe your decision first.")
        else:
            with st.spinner("🔮 Simulating your future..."):
                try:
                    payload = {
                        "decision": decision,
                        "category": category,
                        "budget": budget,
                        "duration": duration,
                        "risk_level": risk_level
                    }
                    resp = requests.post(f"{BACKEND_URL}/simulate", json=payload, timeout=60)
                    resp.raise_for_status()
                    data = resp.json()
                    st.session_state["main_result"] = data
                    st.success("Simulation complete!")
                except Exception as e:
                    st.error(f"Error: {e}")

    if "main_result" in st.session_state:
        render_results(st.session_state["main_result"], label="Primary Scenario")

    # ── What-If Comparison ──
    if compare_btn:
        if not decision.strip():
            st.warning("Please describe your decision first.")
        else:
            with st.spinner("⚡ Running comparison simulation..."):
                try:
                    payload = {
                        "decision": decision,
                        "category": category,
                        "budget": compare_budget,
                        "duration": duration,
                        "risk_level": compare_risk
                    }
                    resp = requests.post(f"{BACKEND_URL}/simulate", json=payload, timeout=60)
                    resp.raise_for_status()
                    data = resp.json()
                    st.session_state["compare_result"] = data
                    st.success("Comparison ready!")
                except Exception as e:
                    st.error(f"Error: {e}")

    if "compare_result" in st.session_state:
        st.divider()
        render_results(st.session_state["compare_result"], label="What-If Scenario")

    # ── Side-by-side summary if both exist ──
    if "main_result" in st.session_state and "compare_result" in st.session_state:
        st.divider()
        st.subheader("⚖️ Head-to-Head Comparison")

        main_r = st.session_state["main_result"]["result"]
        comp_r = st.session_state["compare_result"]["result"]

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Primary Scenario**")
            st.metric("Success %", f"{main_r.get('success_probability', 0)}%")
            st.metric("ROI", f"{main_r.get('financial_outcome', {}).get('roi_percent', 0):.1f}%")
        with col_b:
            st.markdown("**What-If Scenario**")
            st.metric("Success %", f"{comp_r.get('success_probability', 0)}%",
                      delta=str(comp_r.get('success_probability', 0) - main_r.get('success_probability', 0)) + "%")
            st.metric("ROI", f"{comp_r.get('financial_outcome', {}).get('roi_percent', 0):.1f}%",
                      delta=f"{comp_r.get('financial_outcome', {}).get('roi_percent', 0) - main_r.get('financial_outcome', {}).get('roi_percent', 0):.1f}%")
