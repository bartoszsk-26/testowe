# app.py
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide", page_title="Product Accuracy Dashboard")
st.title("📊 Product Accuracy Dashboard")

# -----------------------
# Google Sheet setup
# -----------------------
sheet_id = "1jGmOw9KHLFuAX17577NeGAm7MGgimF8LK2ksdRh3fFY"
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

@st.cache_data(ttl=300)  # cache for 5 minutes
def load_data():
    df = pd.read_csv(url)
    
    # Clean column names: lowercase, remove spaces
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "")
    
    # Rename 'products' to 'product'
    df = df.rename(columns={"products": "product"})
    
    # Validate required columns
    required = {"product", "week2", "week3"}
    missing = required - set(df.columns)
    if missing:
        st.error(f"Missing required columns: {missing}")
        st.stop()
    
    # Calculate change
    df["change"] = df["week3"] - df["week2"]
    
    return df

# Load data
df = load_data()

# -----------------------
# Raw Data Table
# -----------------------
st.subheader("Model results")
st.dataframe(df)

# -----------------------
# Top 5 Products — Largest Change
# -----------------------
st.subheader("Top 5 Products — Largest Increase")
top5 = df.sort_values("change", ascending=False).head(5)
st.dataframe(top5)

# -----------------------
# Average Metrics
# -----------------------
avg_week2 = df["week2"].mean()
avg_week3 = df["week3"].mean()
avg_diff = avg_week3 - avg_week2

col1, col2, col3 = st.columns(3)
col1.metric("Avg Week 2", f"{avg_week2:.2f}%")
col2.metric("Avg Week 3", f"{avg_week3:.2f}%")
col3.metric("Difference", f"{avg_diff:.2f}%")
# ---
st.subheader("🔥 Top Movers")

top_n = st.slider("Select Top N", 1, 20, 5)
trend_type = st.radio("Trend Type", ["Increase", "Decrease"])

if trend_type == "Increase":
    top_df = df.sort_values("change", ascending=False).head(top_n)
else:
    top_df = df.sort_values("change", ascending=True).head(top_n)

cols = st.columns(top_n)
for i, (_, row) in enumerate(top_df.iterrows()):
    cols[i].metric(
        label=f"{row['product']}",
        value=f"{row['change']:+.2f}%",
        delta=f"{row['week3'] - row['week2']:+.2f}%"
    )
# -----------------------
# Trend Classification
# -----------------------
up = (df["change"] > 0).sum()
down = (df["change"] < 0).sum()
no_change = (df["change"] == 0).sum()

trend_df = pd.DataFrame({
    "Trend": ["Up", "Down", "No Change"],
    "Count": [up, down, no_change]
})

st.subheader("📈 Trend Distribution")
st.bar_chart(trend_df.set_index("Trend"))


