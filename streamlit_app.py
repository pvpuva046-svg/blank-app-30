import streamlit as st
import pandas as pd
import altair as alt
import re

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="F&B Global Dashboard & Registry")

# --- DATA LOADING ---
@st.cache_data
def load_data():
    return pd.read_csv("fnb.csv")

data = load_data()

# --- HIGHLY SPECIFIC MEASUREMENT REGISTRY (Consistency Dimension) ---
def check_rigorous_consistency(df):
    registry = []
    
    # Valid continent list for logical consistency
    valid_continents = ['Africa', 'Antarctica', 'Asia', 'Europe', 'North America', 'Oceania', 'South America']
    # Valid units list
    valid_units = ['liter', 'kg', 'dozen', 'unit', 'grams']

    # 2. Define Granular Rules
    rules = {
        "City": {
            "req": "Title Case, no numbers",
            "check": lambda x: str(x).istitle() and not any(char.isdigit() for char in str(x))
        },
        "ISO_Country_Code": {
            "req": "Exactly 3 Uppercase A-Z",
            "check": lambda x: bool(re.match(r'^[A-Z]{3}$', str(x)))
        },
        "Continent": {
            "req": "Must be 1 of 7 official continents",
            "check": lambda x: str(x) in valid_continents
        },
        "Month": {
            "req": "Format YYYY-MM (e.g. 2025-10)",
            "check": lambda x: bool(re.match(r'^\d{4}-(0[1-9]|1[0-2])$', str(x)))
        },
        "Item_Key": {
            "req": "Snake_case (Underscore separated)",
            "check": lambda x: "_" in str(x) and str(x).islower() == False
        },
        "Quantity": {
            "req": "Positive Whole Number (No Decimals)",
            "check": lambda x: (float(x).is_integer() and float(x) > 0) if pd.notnull(x) else False
        },
        "Unit": {
            "req": "Lowercase standard unit names",
            "check": lambda x: str(x) in valid_units
        },
        "Price_USD": {
            "req": "Positive numeric, max 2 decimals",
            "check": lambda x: isinstance(x, (int, float)) and x > 0 and round(float(x), 2) == float(x)
        },
        "Data_Collection_Date": {
            "req": "Format DD/MM/YYYY",
            "check": lambda x: bool(re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', str(x)))
        },
        "Source_URL": {
            "req": "Secure URL (Starts with https://)",
            "check": lambda x: str(x).startswith("https://")
        },
        "Population_Estimate": {
            "req": "Whole number > 0",
            "check": lambda x: (float(x).is_integer() and float(x) > 0) if pd.notnull(x) else False
        }
    }

    # 3. Execute Registry Audit
    for col, rule_info in rules.items():
        if col in df.columns:
            try:
                pass_series = df[col].apply(rule_info["check"])
                pass_count = pass_series.sum()
                pass_rate = (pass_count / len(df)) * 100
                
                registry.append({
                    "Column": col,
                    "Requirement": rule_info["req"],
                    "Score (%)": round(pass_rate, 2),
                    "Status": "✅ PASS" if pass_rate == 100 else "❌ FAILED"
                })
            except:
                registry.append({"Column": col, "Requirement": rule_info["req"], "Score (%)": 0, "Status": "🚨 ERROR"})
    
    return pd.DataFrame(registry)

registry_df = check_rigorous_consistency(data)

# --- SIDEBAR & AGGREGATES ---
st.sidebar.header("Dashboard Controls")
max_price = st.sidebar.slider("Chart Filter: Max Price ($)", 0.0, float(data['Price_USD'].max()), 50.0)

# Main Title & Metrics
st.title("F&B Global Command Center")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Rows Scanned", f"{len(data):,}")
m2.metric("Avg Price", f"${data['Price_USD'].mean():.2f}")
m3.metric("Data Consistency", f"{registry_df['Score (%)'].mean():.1f}%")
m4.metric("Failed Rules", len(registry_df[registry_df["Status"] == "❌ FAILED"]))

st.divider()

# --- SIMULTANEOUS DISPLAY (Tabs for Clarity) ---
tab1, tab2 = st.tabs(["📊 Live Analysis", "🛡 Measurement Registry"])
[29/4/2026 12:47 AM] puvanan: with tab1:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Raw Data Table")
        st.dataframe(data, height=600)
    with c2:
        st.subheader("Visual Trends")
        # Bar Chart
        filtered_bar = data[data['Price_USD'] <= max_price]
        bar = alt.Chart(filtered_bar).mark_bar().encode(
            x=alt.X('Item_Key', sort='-y', title="Item ID"),
            y=alt.Y('Price_USD', title="Price (USD)"),
            color=alt.Color('Price_USD', scale=alt.Scale(scheme='viridis')),
            tooltip=['Item', 'Price_USD', 'City']
        ).properties(height=280)
        
        # Line Chart
        line = alt.Chart(data).mark_line(point=True).encode(
            x=alt.X('Month', title="Timeline"),
            y=alt.Y('mean(Price_USD)', title="Avg Price"),
            color=alt.value("#FFA500")
        ).properties(height=280)
        
        st.altair_chart(bar, use_container_width=True)
        st.altair_chart(line, use_container_width=True)

with tab2:
    st.subheader("Registry: Consistency Dimension")
    st.markdown("Detailed breakdown of data quality rules and their enforcement status.")
    
    # Custom Row Coloring
    def color_rows(row):
        color = 'background-color: #e6ffed' if 'PASS' in row.Status else 'background-color: #ffeef0'
        return [color] * len(row)

    st.dataframe(registry_df.style.apply(color_rows, axis=1), use_container_width=True)
