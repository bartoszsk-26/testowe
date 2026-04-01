import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pyngrok import ngrok
import threading
import subprocess
import time
import sys
import os

# -----------------------
# NGROK SETUP
# -----------------------
NGROK_AUTH = "username:password"  # <-- change this
STREAMLIT_PORT = 8501

def start_ngrok():
    public_url = ngrok.connect(STREAMLIT_PORT, "http", auth=NGROK_AUTH)
    print(f"🔗 Streamlit is publicly available at: {public_url}")
    print("Use username/password to login via ngrok.")

# Only start ngrok if running locally
if "get_ipython" not in globals():  # not in Jupyter
    threading.Thread(target=start_ngrok, daemon=True).start()
    time.sleep(1)  # wait a bit so ngrok tunnel is established

st.set_page_config(layout="wide", page_title="Product Dashboard")
st.title("📊 Product Accuracy Dashboard")

# -----------------------
# Google Sheet URLs
# -----------------------
sheet_id = "1jGmOw9KHLFuAX17577NeGAm7MGgimF8LK2ksdRh3fFY"

url1 = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
url2 = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=157430345"


# -----------------------
# LOAD SHEET 1
# -----------------------
@st.cache_data(ttl=60)
def load_sheet1():
    df = pd.read_csv(url1)

    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "", regex=False)
        .str.replace("\ufeff", "", regex=False)
    )

    df = df.rename(columns={"products": "product"})

    df["week2"] = pd.to_numeric(df["week2"], errors="coerce")
    df["week3"] = pd.to_numeric(df["week3"], errors="coerce")

    df["change"] = df["week3"] - df["week2"]

    return df


# -----------------------
# LOAD SHEET 2
# -----------------------
@st.cache_data(ttl=60)
def load_sheet2():
    df = pd.read_csv(url2)

    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "", regex=False)
        .str.replace("\ufeff", "", regex=False)
    )

    # auto detect product id column
    for col in df.columns:
        if "id" in col:
            df = df.rename(columns={col: "productid"})

    df["accuracy"] = pd.to_numeric(df["accuracy"], errors="coerce")

    return df


df1 = load_sheet1()
df2 = load_sheet2()

# -----------------------
# TABS
# -----------------------
tab1, tab2 = st.tabs(["Top Movers (Sheet1)", "Monthly Accuracy (Sheet2)"])


# =====================================================
# TAB 1 — TOP MOVERS
# =====================================================
with tab1:
    st.subheader("Filters")

options = st.multiselect(
    "What are your favorite colors?",
    ["Green", "Yellow", "Red", "Blue"],
    default=["Yellow", "Red"],
)

st.write("You selected:", options)

    # ---------------- KPI TOP MOVERS ----------------
    st.subheader("🔥 Top Movers KPI Cards")

    top_n = st.slider("Select Top N", 1, 20, 5)
    trend_type = st.radio("Trend Type", ["Increase", "Decrease"])

    if trend_type == "Increase":
        top_df = filtered_df1.sort_values("change", ascending=False).head(top_n)
    else:
        top_df = filtered_df1.sort_values("change").head(top_n)

    cols = st.columns(len(top_df))

    for i, (_, row) in enumerate(top_df.iterrows()):
        cols[i].metric(
            label=str(row["product"]),
            value=f"{row['change']:+.2f}%",
            delta=f"{row['change']:+.2f}%"
        )

    # ---------------- CHART ----------------
    st.subheader("Change per Product")
    st.bar_chart(filtered_df1.set_index("product")["change"])

    # ---------------- AVERAGES ----------------
    avg_week2 = filtered_df1["week2"].mean()
    avg_week3 = filtered_df1["week3"].mean()

    col1, col2, col3 = st.columns(3)
    col1.metric("Avg Week 2", f"{avg_week2:.2f}%")
    col2.metric("Avg Week 3", f"{avg_week3:.2f}%")
    col3.metric("Difference", f"{(avg_week3-avg_week2):.2f}%")

    # ---------------- TRENDS ----------------
    up = (filtered_df1["change"] > 0).sum()
    down = (filtered_df1["change"] < 0).sum()
    no_change = (filtered_df1["change"] == 0).sum()

    trend_df = pd.DataFrame({
        "Trend": ["Up", "Down", "No Change"],
        "Count": [up, down, no_change]
    })

    st.subheader("📈 Trend Distribution")
    st.bar_chart(trend_df.set_index("Trend"))


# =====================================================
# TAB 2 — MONTHLY ACCURACY
# =====================================================
with tab2:

    st.subheader("Filters")

    regions2 = sorted(df2["region"].dropna().unique())

    selected_region2 = st.selectbox(
        "Choose Region",
        ["All"] + list(regions2),
        key="region_tab2"
    )

    if selected_region2 == "All":
        filtered_df2 = df2.copy()
    else:
        filtered_df2 = df2[df2["region"] == selected_region2]

    st.write("You selected:", selected_region2)

    # ---------------- KPI METRICS ----------------
    total_products = filtered_df2["productid"].nunique()
    above_95 = (filtered_df2["accuracy"] > 95).sum()
    below_95 = (filtered_df2["accuracy"] < 95).sum()
    exact_100 = (filtered_df2["accuracy"] == 100).sum()
    avg_accuracy = filtered_df2["accuracy"].mean()

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Total Products", total_products)
    col2.metric("Above 95%", above_95)
    col3.metric("Below 95%", below_95)
    col4.metric("100% Accuracy", exact_100)
    col5.metric("Average Accuracy", f"{avg_accuracy:.2f}%")

    # ---------------- PIE CHART ----------------
    counts = [above_95, below_95, exact_100]
    labels = [">95%", "<95%", "100%"]

    fig1, ax1 = plt.subplots()
    ax1.pie(counts, labels=labels, autopct="%1.1f%%", startangle=90)
    ax1.axis("equal")

    st.subheader("Product Accuracy Distribution")
    st.pyplot(fig1)

    # ---------------- REGION AVG ----------------
    region_avg = (
        filtered_df2.groupby("region")["accuracy"]
        .mean()
        .sort_values(ascending=False)
    )

    st.subheader("Average Accuracy by Region")
    st.bar_chart(region_avg)

    # ---------------- HISTOGRAM ----------------
    st.subheader("Accuracy Histogram")
    st.bar_chart(filtered_df2["accuracy"].value_counts().sort_index())
