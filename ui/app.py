"""
ExaGuard - Simple Investigation UI
"""
import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="ExaGuard", page_icon="🛡️", layout="wide")

st.title("🛡️ ExaGuard")
st.markdown("**Evidence-first financial crime topology investigations on Exasol Personal**")

# Sidebar
st.sidebar.header("Actions")
if st.sidebar.button("🔄 Check API Health"):
    try:
        r = requests.get(f"{API_URL}/api/v1/health", timeout=5)
        st.sidebar.json(r.json())
    except Exception as e:
        st.sidebar.error(f"Cannot connect: {e}")

if st.sidebar.button("🔍 Run Detection"):
    try:
        r = requests.post(f"{API_URL}/api/v1/detect", timeout=30)
        st.sidebar.success(f"Detection finished: {r.json()}")
    except Exception as e:
        st.sidebar.error(str(e))

# Main content
tab1, tab2, tab3 = st.tabs(["Evidence", "Transactions", "Accounts"])

with tab1:
    st.subheader("Stored Evidence")
    try:
        r = requests.get(f"{API_URL}/api/v1/evidence", timeout=10)
        data = r.json()
        if data:
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("No evidence yet. Click 'Run Detection' in the sidebar.")
    except Exception as e:
        st.warning(f"Could not load evidence: {e}")

with tab2:
    st.subheader("Recent Transactions")
    try:
        r = requests.get(f"{API_URL}/api/v1/transactions?limit=50", timeout=10)
        st.dataframe(pd.DataFrame(r.json()), use_container_width=True)
    except Exception as e:
        st.warning(f"Could not load transactions: {e}")

with tab3:
    st.subheader("Accounts")
    try:
        r = requests.get(f"{API_URL}/api/v1/accounts?limit=30", timeout=10)
        st.dataframe(pd.DataFrame(r.json()), use_container_width=True)
    except Exception as e:
        st.warning(f"Could not load accounts: {e}")

st.markdown("---")
st.caption("ExaGuard • Built for Exasol AI + Data Challenge 2026")