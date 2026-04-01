# app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide", page_title="Product Dashboard")
st.title("📊 Product Accuracy Dashboard")

# -----------------------
# Google Sheet URLs
# -----------------------
sheet_id = "1jGmOw9KHLFuAX17577NeGAm7MGgimF8LK2ksdRh3fFY"
# Sheet 1: Arkusz1
url1 = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
# Sheet 2: Arkusz 2
url2 = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=157430345"

# -----------------------
# Load data
# -----------------------
@st.cache_data(ttl=60)
def load_sheet1():
    df = pd.read_csv(url1)

    # clean headers safely
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "", regex=False)
        .str.replace("\ufeff", "", regex=False)
    )

    # rename columns
    df = df.rename(columns={
        "products": "product",
        "week2": "week2",
        "week3": "week3",
        "region": "region"
    })

    # numeric safety
    df["week2"] = pd.to_numeric(df["week2"], errors="coerce")
    df["week3"] = pd.to_numeric(df["week3"], errors="coerce")

    # calculate change
    df["change"] = df["week3"] - df["week2"]

    return df

# -----------------------
# Tabs for each sheet
# -----------------------
tab1, tab2 = st.tabs(["Top Movers (Sheet1)", "Monthly Accuracy (Sheet2)"])

# -----------------------
# TAB 1: Top Movers
# -----------------------
with tab1:
    # -----------------------
# REGION FILTER (Sheet1)
# -----------------------
st.subheader("Filters")

regions1 = sorted(filtered_df1["region"].dropna().unique())

selected_region1 = st.selectbox(
    "Choose Region",
    ["All"] + list(regions1),
    key="region_tab1"
)

# Apply filter
if selected_region1 == "All":
    filtered_filtered_df1 = filtered_df1.copy()
else:
    filtered_filtered_df1 = filtered_df1[filtered_df1["region"] == selected_region1]

st.write("You selected:", selected_region1)
    st.subheader("🔥 Top Movers KPI Cards")
    top_n = st.slider("Select Top N", 1, 20, 5)
    trend_type = st.radio("Trend Type", ["Increase", "Decrease"])

    if trend_type == "Increase":
        top_df = filtered_df1.sort_values("change", ascending=False).head(top_n)
    else:
        top_df = filtered_df1.sort_values("change", ascending=True).head(top_n)

    cols = st.columns(top_n)
    for i, (_, row) in enumerate(top_df.iterrows()):
        cols[i].metric(
            label=f"{row['product']}",
            value=f"{row['change']:+.2f}%",
            delta=f"{row['week3'] - row['week2']:+.2f}%"
        )

    st.subheader("Change per Product")
    st.bar_chart(filtered_df1.set_index("product")["change"])

    # Average metrics
    avg_week2 = filtered_df1["week2"].mean()
    avg_week3 = filtered_df1["week3"].mean()
    avg_diff = avg_week3 - avg_week2

    col1, col2, col3 = st.columns(3)
    col1.metric("Avg Week 2", f"{avg_week2:.2f}%")
    col2.metric("Avg Week 3", f"{avg_week3:.2f}%")
    col3.metric("Difference", f"{avg_diff:.2f}%")

    # Trend classification
    up = (filtered_df1["change"] > 0).sum()
    down = (filtered_df1["change"] < 0).sum()
    no_change = (filtered_df1["change"] == 0).sum()

    trend_df = pd.DataFrame({
        "Trend": ["Up", "Down", "No Change"],
        "Count": [up, down, no_change]
    })

    st.subheader("📈 Trend Distribution")
    st.bar_chart(trend_df.set_index("Trend"))

# -----------------------
# TAB 2: Monthly Accuracy
# -----------------------
with tab2:
    st.subheader("📊 Monthly Accuracy Metrics")

    # Total unique products
    total_products = df2["productid"].nunique()
    # Products above 95%
    above_95 = (df2["accuracy"] > 95).sum()
    # Products below 95%
    below_95 = (df2["accuracy"] < 95).sum()
    # Products with 100% accuracy
    exact_100 = (df2["accuracy"] == 100).sum()
    # Average accuracy
    avg_accuracy = df2["accuracy"].mean()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Products", total_products)
    col2.metric("Above 95%", above_95)
    col3.metric("Below 95%", below_95)
    col4.metric("100% Accuracy", exact_100)
    col5.metric("Average Accuracy", f"{avg_accuracy:.2f}%")

    # Pie chart for distribution
    counts = [above_95, below_95, exact_100]
    labels = [">95%", "<95%", "100%"]
    colors = ["#2ca02c", "#d62728", "#1f77b4"]

    fig1, ax1 = plt.subplots()
    ax1.pie(counts, labels=labels, autopct="%1.1f%%", colors=colors, startangle=90)
    ax1.axis("equal")
    st.subheader("Product Accuracy Distribution")
    st.pyplot(fig1)

    # Average accuracy by region
    region_avg = df2.groupby("region")["accuracy"].mean().sort_values(ascending=False)
    st.subheader("Average Accuracy by Region")
    st.bar_chart(region_avg)

    # Histogram of accuracy
    st.subheader("Accuracy Histogram")
    st.bar_chart(df2["accuracy"].value_counts().sort_index())
